"""This module implements different readers for package files."""

from io import IOBase
from Bcfg2.Compat import walk_packages


def get_readers():
    """ Return all available packages readers. """
    return [m[1]  # pylint: disable=C0103
            for m in walk_packages(path=__path__)]


class Reader(IOBase):
    extension = None

    def __init__(self, name):
        self.name = name
        self._file = self._open(name)

    def _open(self, filename):
        raise NotImplementedError

    def read(self, size=-1):
        return self._file.read(size)

    def readable(self):
        return self._file.readable()

    def readline(self, size=-1):
        return self._file.readline(size)

    def readlines(self, hint=None):
        return self._file.readlines(size)

    def writelines(self, lines):
        self._unsupported("writelines")
