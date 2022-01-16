""" Reader for uncompressed package sources. """

from Bcfg2.Server.Plugins.Packages.Readers import Reader


class NoneReader(Reader):
    extension = ''

    def _open(self, filename):
        return open(filename)
