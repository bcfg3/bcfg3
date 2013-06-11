import os
import re
import sys
import copy
import logging
import lxml.etree
import Bcfg2.Server.Plugin

logger = logging.getLogger('Bcfg2.Plugins.PkgVars')
vars = ['pin', 'use', 'keywords']

class PkgVarsFile(Bcfg2.Server.Plugin.StructFile):
    def get_additional_data(self, meta):
        data = self.Match(meta)
        results = {}
        for d in data:
            name = d.get('name', '')

            for v in vars:
                value = d.get(v, None)
                if value:
                    results[v][name] = value

        return results

class PkgVarsDirectoryBacked(Bcfg2.Server.Plugin.DirectoryBacked):
    __child__ = PkgVarsFile
    patterns = re.compile(r'.*\.xml$')

    def get_additional_data(self, meta):
        results = {}
        for v in vars:
            results[v] = {}

        for files in self.entries:
            new = self.entries[files].get_additional_data(meta)
            for x in vars:
                results[x].update(new[x])

        return results

class PkgVars(Bcfg2.Server.Plugin.Plugin,
              Bcfg2.Server.Plugin.Connector):
    name = 'PkgVars'
    version = '$Revision$'

    def __init__(self, core):
        Bcfg2.Server.Plugin.Plugin.__init__(self, core)
        Bcfg2.Server.Plugin.Connector.__init__(self)
        try:
            self.store = PkgVarsDirectoryBacked(self.data)
        except OSError:
            e = sys.exc_info()[1]
            self.logger.error("Error while creating PkgVars store: %s %s" %
                              (e.strerror, e.filename))
            raise Bcfg2.Server.Plugin.PluginInitError

    def get_additional_data(self, meta):
        return self.store.get_additional_data(meta)
