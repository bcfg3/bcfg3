""" Dummy backend for :mod:`Bcfg2.Server.Plugins.Packages` """

from Bcfg2.Server.Plugins.Packages.Collection import Collection
from Bcfg2.Server.Plugins.Packages.Source import Source


class DummyCollection(Collection):
    """ Handle collections of Dummy sources.  This is a no-op object
    that simply inherits from
    :class:`Bcfg2.Server.Plugins.Packages.Collection.Collection`,
    overrides nothing, and defers all operations to :class:`PacSource`
    """

    def __init__(self, metadata, sources, cachepath, basepath, debug=False):
        # we define an __init__ that just calls the parent __init__,
        # so that we can set the docstring on __init__ to something
        # different from the parent __init__ -- namely, the parent
        # __init__ docstring, minus everything after ``.. -----``,
        # which we use to delineate the actual docs from the
        # .. autoattribute hacks we have to do to get private
        # attributes included in sphinx 1.0 """
        Collection.__init__(self, metadata, sources, cachepath, basepath,
                            debug=debug)
    __init__.__doc__ = Collection.__init__.__doc__.split(".. -----")[0]


class DummySource(Source):
    """ Handle Dummy sources """

    #: DummySource sets the ``type`` on Package entries to "dummy"
    ptype = 'dummy'

    def __init__(self, basepath, xsource):
        xsource.set('rawurl', 'http://example.com/')
        Source.__init__(self, basepath, xsource)
