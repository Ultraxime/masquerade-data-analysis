# -*- coding: utf-8 -*-
# @Author: Ultraxime
# @Last Modified by:   Ultraxime
# @Last Modified time: 2023-08-18 13:20:25
#
# This file is part of Masquerade Data Analysis.
#
# Masquerade Data Analysis is free software: you can redistribute it and/or modify it
# under the terms of the GNU General Public License as published by the
# Free Software Foundation, either version 3 of the License, or any later version.
#
# Masquerade Data Analysis is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty
# of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.
# See the GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Masquerade Data Analysis. If not, see <https://www.gnu.org/licenses/>.
"""
Module for the custom loader
"""
from yaml import SafeLoader
from yaml.nodes import MappingNode

from .types import BrowserTime
from .types import BulkTest
from .types import Report
from .types import SpeedTest


# pylint: disable=R0901     # Too many ancestors
class Loader(SafeLoader):
    """
    This class describes a loader to load our custom types.
    """
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.deep_construct = True
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
