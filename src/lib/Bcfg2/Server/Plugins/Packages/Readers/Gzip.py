""" Reader for gzip compressed package sources. """

import gzip
from Bcfg2.Server.Plugins.Packages.Readers import Reader


class GzipReader(Reader):
    extension = 'gz'

    def _open(self, filename):
        return gzip.GzipFile(filename)
