""" Compatibility imports, mostly for Py3k support, but also for
Python 2.4 and such-like """

###################################################
#                                                 #
#   IF YOU ADD SOMETHING TO THIS FILE, YOU MUST   #
#   DOCUMENT IT IN docs/development/compat.txt    #
#                                                 #
###################################################

import sys

# pylint: disable=E0601,E0602,E0611,W0611,W0622,C0103

from email.utils import formatdate

# urllib imports
from urllib.parse import quote_plus
from urllib.request import urlretrieve
from urllib.parse import urljoin, urlparse
from urllib.request import HTTPBasicAuthHandler, HTTPPasswordMgrWithDefaultRealm, build_opener, install_opener, urlopen
from urllib.error import HTTPError, URLError

from io import StringIO

import configparser as ConfigParser

import pickle as cPickle

from queue import Queue, Empty, Full

# xmlrpc imports
import xmlrpc.client as xmlrpclib
import xmlrpc.server as SimpleXMLRPCServer

# socketserver import
import socketserver as SocketServer

# httplib imports
import http.client as httplib

try:
    str = str
except NameError:
    str = str


def u_str(string, encoding=None):
    """ print to file compatibility """
    if sys.hexversion >= 0x03000000:
        return string
    else:
        if encoding is not None:
            return str(string, encoding)
        else:
            return str(string)


def ensure_binary(string, encoding='utf-8'):
    if type(string) == str:
        return string.encode(encoding)
    return string


from functools import wraps

# base64 compat
from base64 import b64encode as _b64encode, b64decode as _b64decode


# the b64 encoded data are ASCII strings, but the decoded data can be
# arbitrary bytes, which are not necessarily meaningful in the context
# of any encoding
@wraps(_b64encode)
def b64encode(val, **kwargs):  # pylint: disable=C0111
    try:
        return _b64encode(val, **kwargs)
    except TypeError:
        return _b64encode(val.encode('UTF-8'), **kwargs).decode('ascii')

@wraps(_b64decode)
def b64decode(val, **kwargs):  # pylint: disable=C0111
    return _b64decode(val.encode('ascii'), **kwargs)


input = input


from functools import reduce


from collections.abc import MutableMapping


class CmpMixin(object):
    """ In Py3K, :meth:`object.__cmp__` is no longer magical, so this
    mixin can be used to define the rich comparison operators from
    ``__cmp__`` -- i.e., it makes ``__cmp__`` magical again. """

    def __lt__(self, other):
        return self.__cmp__(other) < 0

    def __gt__(self, other):
        return self.__cmp__(other) > 0

    def __eq__(self, other):
        return self.__cmp__(other) == 0

    def __ne__(self, other):
        return not self.__eq__(other)

    def __ge__(self, other):
        return self.__gt__(other) or self.__eq__(other)

    def __le__(self, other):
        return self.__lt__(other) or self.__eq__(other)


from pkgutil import walk_packages


all = all
any = any


from hashlib import md5


def oct_mode(mode):
    """ Convert a decimal number describing a POSIX permissions mode
    to a string giving the octal mode.  In Python 2, this is a synonym
    for :func:`oct`, but in Python 3 the octal format has changed to
    ``0o000``, which cannot be used as an octal permissions mode, so
    we need to strip the 'o' from the output.  I.e., this function
    acts like the Python 2 :func:`oct` regardless of what version of
    Python is in use.

    :param mode: The decimal mode to convert to octal
    :type mode: int
    :returns: string """
    return oct(mode).replace('o', '')


long = int


def cmp(a, b):
    """ Py3k implementation of cmp() """
    return (a > b) - (a < b)


from ast import literal_eval
