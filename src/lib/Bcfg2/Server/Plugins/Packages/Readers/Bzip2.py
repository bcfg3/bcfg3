""" Reader for bzip2 compressed package sources. """

import bz2
from Bcfg2.Server.Plugins.Packages.Readers import Reader


class Bzip2Reader(Reader):
    extension = 'bz'

    def _open(self, filename):
        return bz2.BZ2File(filename)

    def readable(self):
        return True
