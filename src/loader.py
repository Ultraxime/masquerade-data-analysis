"""
Module for the custom loader
"""

from yaml import SafeLoader
from yaml.nodes import MappingNode

from .types import SpeedTest, BulkTest, BrowserTime, Report


# pylint: disable=R0901     # Too many ancestors
class Loader(SafeLoader):
    """
    This class describes a loader to load our custom types.
    """
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.add_constructor("tag:yaml.org,2002:python/object:speedtest.SpeedTest",
                             self.constructor(SpeedTest))
        self.add_constructor("tag:yaml.org,2002:python/object:bulktest.BulkTest",
                             self.constructor(BulkTest))
        self.add_constructor("tag:yaml.org,2002:python/object:browsertime.BrowserTime",
                             self.constructor(BrowserTime))
        self.add_constructor("tag:yaml.org,2002:python/object:browsertime.Report",
                             self.constructor(Report))

    def constructor(self, cls):
        """
        Create a contructor for the type
        
        :param      cls:  The cls
        :type       cls:  type
        
        :returns:   a constructor
        :rtype:     SafeLoader -> MappingNode -> cls
        """
        def tmp(loader: SafeLoader, node: MappingNode):
            return cls(**loader.construct_mapping(node))
        return tmp
