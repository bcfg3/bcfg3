""" Reader for lzma compressed package sources. """

import lzma
from Bcfg2.Server.Plugins.Packages.Readers import Reader


class XzReader(Reader):
    extension = 'xz'

    def _open(self, filename):
        return lzma.LZMAFile(filename)
