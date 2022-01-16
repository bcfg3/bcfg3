"""This is the Bcfg2 tool for the Dummy package system."""

import re
import Bcfg2.Client.Tools


class Dummy(Bcfg2.Client.Tools.PkgTool):
    __handles__ = [('Package', 'dummy')]
    __req__ = {'Package': []}
    pkgtype = 'dummy'

    def RefreshPackages(self):
        pass

    def VerifyPackage(self, _entry, _):
        return True
