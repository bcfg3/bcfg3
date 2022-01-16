"""
APT backend for :mod:`Bcfg2.Server.Plugins.Packages` using
apt_pkg python bindings.
"""

import apt_pkg
from Bcfg2.Server.Plugins.Packages.Apt import AptCollection, AptSource


class PyaptCollection(AptCollection):
    """ Handle collections of PyAPT sources.  This is a no-op object
    that simply inherits from
    :class:`Bcfg2.Server.Plugins.Packages.Apt.AptCollection` and
    overrides nothing.
    """
    pass


class PyaptSource(AptSource):
    """ Handle PyAPT sources """

    def read_files(self):  # pylint: disable=R0912
        bdeps = dict()
        brecs = dict()
        bprov = dict()
        bvers = dict()
        self.pkgnames = set()
        self.essentialpkgs = set()
        for fname in self.files:
            barch = self._get_arch(fname)
            if barch not in bdeps:
                bdeps[barch] = dict()
                brecs[barch] = dict()
                bprov[barch] = dict()

            apt_pkg.init_system()
            with apt_pkg.TagFile(fname) as tagfile:
                for section in tagfile:
                    pkgname = section['Package']

                    if pkgname in bvers:
                        new = section['Version']
                        old = bvers[pkgname]
                        if apt_pkg.version_compare(new, old) <= 0:
                            continue

                    self.pkgnames.add(pkgname)
                    bvers[pkgname] = section['Version']
                    bdeps[barch][pkgname] = []
                    brecs[barch][pkgname] = []

                    if section.find_flag('Essential'):
                        self.essentialpkgs.add(pkgname)

                    for dep_type in ['Depends', 'Pre-Depends', 'Recommends']:
                        dep_str = section.find(dep_type)
                        if dep_str is None:
                            continue

                        vindex = 0
                        for dep in apt_pkg.parse_depends(dep_str):
                            if len(dep) > 1:
                                cdeps = [cdep for (cdep, _, _) in dep]
                                dyn_dname = "choice-%s-%s-%s" % (pkgname,
                                                                 barch,
                                                                 vindex)
                                vindex += 1

                                if dep_type == 'Recommends':
                                    brecs[barch][pkgname].append(dyn_dname)
                                else:
                                    bdeps[barch][pkgname].append(dyn_dname)
                                bprov[barch][dyn_dname] = set(cdeps)
                            else:
                                (raw_dep, _, _) = dep[0]
                                if dep_type == 'Recommends':
                                    brecs[barch][pkgname].append(raw_dep)
                                else:
                                    bdeps[barch][pkgname].append(raw_dep)

                    provides = section.find('Provides')
                    if provides is not None:
                        provided_packages = [
                                pkg
                                for group in apt_pkg.parse_depends(provides)
                                for (pkg, _, _) in group]
                        for dname in provided_packages:
                            if dname not in bprov[barch]:
                                bprov[barch][dname] = set()
                            bprov[barch][dname].add(pkgname)

        self.process_files(bdeps, bprov, brecs)
    read_files.__doc__ = AptSource.read_files.__doc__
