#!/usr/bin/env python

import os
os.environ['BCFG2_LEGACY_MODELS'] = '1'

import sys
import logging
import time
import Bcfg2.Logger
import Bcfg2.Options
from Bcfg2.DBSettings import get_db_label
import django
from django.db import transaction, connections
from Bcfg2.Server.Admin import UpdateReports
from Bcfg2.Reporting.utils import BatchFetch
from Bcfg2.Reporting.Compat import transaction

logger = logging.getLogger(__name__)

_our_backend = None


def _quote(value):
    """
    Quote a string to use as a table name or column

    Newer versions and various drivers require an argument
    https://code.djangoproject.com/ticket/13630
    """
    global _our_backend
    if not _our_backend:
        _our_backend = connections[get_db_label('Reporting')].ops
    return _our_backend.quote_name(value)


@transaction.atomic
def _migrate_perms():
    """helper"""

    fperms = {}

    logger.info("Creating FilePerms objects")
    for data in (('owner', 'group', 'perms'),
            ('current_owner', 'current_group', 'current_perms')):
        for grp in legacy_models.Reason.objects.values_list(*data).distinct():
            if grp in fperms:
                continue
            fp = new_models.FilePerms(owner=grp[0], group=grp[1], mode=grp[2])
            fp.save()
            fperms[grp] = fp

    return fperms


@transaction.atomic
def _migrate_transaction(inter, entries, fperms):
    """helper"""

    logger.debug("Migrating interaction %s for %s" %
        (inter.id, inter.client.name))

    newint = new_models.Interaction(id=inter.id,
        client_id=inter.client_id,
        timestamp=inter.timestamp,
        state=inter.state,
        repo_rev_code=inter.repo_rev_code,
        server=inter.server,
        good_count=inter.goodcount,
        total_count=inter.totalcount,
        bad_count=inter.bad_entries,
        modified_count=inter.modified_entries,
        extra_count=inter.extra_entries)

    groups = []
    bundles = []
    try:
        if inter.metadata:
            newint.profile_id = inter.metadata.profile.id
            groups = [grp.pk for grp in inter.metadata.groups.all()]
            bundles = [bun.pk for bun in inter.metadata.bundles.all()]
    except ObjectDoesNotExist:
        pass
    super(new_models.Interaction, newint).save()
    if bundles:
        newint.bundles.add(*bundles)
    if groups:
        newint.groups.add(*groups)

    updates = dict(paths=[], packages=[], actions=[], services=[])
    for ei in legacy_models.Entries_interactions.objects.select_related('reason')\
            .filter(interaction=inter):
        ent = entries[ei.entry_id]
        name = ent.name
        act_dict = dict(name=name, exists=ei.reason.current_exists,
            state=ei.type)

        if ent.kind == 'Action':
            act_dict['status'] = ei.reason.status
            if not act_dict['status']:
                act_dict['status'] = "check"
            act_dict['output'] = -1
            logger.debug("Adding action %s" % name)
            updates['actions'].append(new_models.ActionEntry.entry_get_or_create(act_dict))

        elif ent.kind == 'Package':
            act_dict['target_version'] = ei.reason.version
            act_dict['current_version'] = ei.reason.current_version
            logger.debug("Adding package %s %s" %
                (name, act_dict['target_version']))
            updates['packages'].append(new_models.PackageEntry.entry_get_or_create(act_dict))
        elif ent.kind == 'Path':
            # these might be hard.. they aren't one to one with the old model
            act_dict['path_type'] = 'file'

            act_dict['target_perms'] = fperms[(
                ei.reason.owner,
                ei.reason.group,
                ei.reason.perms
            )]

            act_dict['current_perms'] = fperms[(
                ei.reason.current_owner,
                ei.reason.current_group,
                ei.reason.current_perms
            )]

            if ei.reason.to:
                act_dict['path_type'] = 'symlink'
                act_dict['target_path'] = ei.reason.to
                act_dict['current_path'] = ei.reason.current_to
                logger.debug("Adding link %s" % name)
                updates['paths'].append(new_models.LinkEntry.entry_get_or_create(act_dict))
                continue

            act_dict['detail_type'] = new_models.PathEntry.DETAIL_UNUSED
            if ei.reason.unpruned:
                # this is the only other case we know what the type really is
                act_dict['path_type'] = 'directory'
                act_dict['detail_type'] = new_models.PathEntry.DETAIL_PRUNED
                act_dict['details'] = ei.reason.unpruned

            if ei.reason.is_sensitive:
                act_dict['detail_type'] = new_models.PathEntry.DETAIL_SENSITIVE
            elif ei.reason.is_binary:
                act_dict['detail_type'] = new_models.PathEntry.DETAIL_BINARY
                act_dict['details'] = ei.reason.current_diff
            elif ei.reason.current_diff:
                act_dict['detail_type'] = new_models.PathEntry.DETAIL_DIFF
                act_dict['details'] = ei.reason.current_diff
            logger.debug("Adding path %s" % name)
            updates['paths'].append(new_models.PathEntry.entry_get_or_create(act_dict))

        elif ent.kind == 'Service':
            act_dict['target_status'] = ei.reason.status
            act_dict['current_status'] = ei.reason.current_status
            logger.debug("Adding service %s" % name)
            updates['services'].append(new_models.ServiceEntry.entry_get_or_create(act_dict))
        else:
            logger.warn("Skipping type %s" % ent.kind)

    for entry_type in updates.keys():
        i = 0
        while(i < len(updates[entry_type])):
            getattr(newint, entry_type).add(*updates[entry_type][i:i + 100])
            i += 100

    for perf in inter.performance_items.all():
        new_models.Performance(
            interaction=newint,
            metric=perf.metric,
            value=perf.value).save()


def _shove(old_table, new_table, columns):
    cols = ",".join([_quote(f) for f in columns])
    sql = "insert into %s(%s) select %s from %s" % (
        _quote(new_table),
        cols,
        cols,
        _quote(old_table))

    cursor = connections[get_db_label('Reporting')].cursor()
    cursor.execute(sql)
    cursor.close()


@transaction.atomic
def migrate_stage1():
    logger.info("Migrating clients")
    try:
        _shove(legacy_models.Client._meta.db_table, new_models.Client._meta.db_table,
            ('id', 'name', 'creation', 'expiration'))
    except:
        logger.error("Failed to migrate clients", exc_info=1)
        return False

    logger.info("Migrating Bundles")
    try:
        _shove(legacy_models.Bundle._meta.db_table, new_models.Bundle._meta.db_table,
            ('id', 'name'))
    except:
        logger.error("Failed to migrate bundles", exc_info=1)
        return False

    logger.info("Migrating Groups")
    try:
        _shove(legacy_models.Group._meta.db_table, new_models.Group._meta.db_table,
            ('id', 'name', 'profile', 'public', 'category', 'comment'))
    except:
        logger.error("Failed to migrate groups", exc_info=1)
        return False
    return True


def _restructure():
    """major restructure of reporting data"""

    # run any migrations from the previous schema
    try:
        from Bcfg2.Server.Reports.updatefix import update_database
        update_database()
    except:
        logger.error("Failed to run legacy schema updates", exc_info=1)
        return False

    # try to avoid dangling transactions
    if not migrate_stage1():
        return

    try:
        entries = {}
        for ent in legacy_models.Entries.objects.all():
            entries[ent.id] = ent
    except:
        logger.error("Failed to populate entries dict", exc_info=1)
        return False

    try:
        fperms = _migrate_perms()
    except:
        logger.error("Failed create FilePerms objects", exc_info=1)
        return False

    failures = []
    int_count = legacy_models.Interaction.objects.count()
    if int_count == 0:
        logger.error("Found no legacy interactions")
        return False
    int_ctr = 0
    start_time = 0
    for inter in BatchFetch(legacy_models.Interaction.objects.\
            select_related('metadata', 'client').all()):
        if int_ctr % 1000 == 0:
            if int_ctr > 0:
                logger.info("Migrated %s of %s interactions in %ss" % \
                    (int_ctr, int_count, time.time() - start_time))
            else:
                logger.info("Migrating interactions")
            start_time = time.time()
        try:
            _migrate_transaction(inter, entries, fperms)
        except:
            logger.error("Failed to migrate interaction %s for %s" %
                (inter.id, inter.client.name), exc_info=1)
            failures.append(inter.id)
        int_ctr += 1
    if not failures:
        logger.info("Successfully restructured reason data")
        return True

    logger.info("Updating recent interactions")
    for newint in new_models.Interaction.objects.recent():
        try:
            newint.save()
        except:
            logger.error("Failed to set current interaction %s for %s" %
                (newint.id, newint.client.name), exc_info=1)


if __name__ == '__main__':
    parser = Bcfg2.Options.get_parser(
        description="Migrate from Bcfg2 1.2 DBStats plugin to 1.3 Reporting "
        "subsystem",
        components=[UpdateReports])
    parser.parse()

    from Bcfg2.Reporting import models as new_models
    from Bcfg2.Server.Reports.reports import models as legacy_models
    UpdateReports().run(Bcfg2.Options.setup)
    _restructure()
