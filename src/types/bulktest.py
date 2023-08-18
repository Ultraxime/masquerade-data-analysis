# -*- coding: utf-8 -*-
# @Author: Ultraxime
# @Last Modified by:   Ultraxime
# @Last Modified time: 2023-08-18 14:58:45
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
Module for the bulk test result
"""
from typing import Dict
from typing import List

from .result import Result
from .result import Run


# pylint: disable=R0903
class BulkTestRun(Run):
    """
    This class describes a bulk test run.
    """
    def get_metric(self, metric: str) -> float | str:
        match metric.lower():
            case "bulkdownload":
                res = int(self._content)/1000000
            case _:
                raise ValueError
        if res == 0:
            return "NULL"
        return res


class BulkTest(Result):
    """
    This class describes a bulk test's result.
    """
    def __init__(self, folder: str = ".", name: str = "bulk_download",
                 run_constructor=BulkTestRun, **kwargs):
        super().__init__(folder, name, run_constructor, **kwargs)

    def plot(self):
        self.subplot("bulk download", unit="mbps",
                     convert=lambda x : [int(x) / 1000000], scale="log")

    def get_download(self) -> Dict[str, List[float]]:
        """
        Gets the download speed.

        :returns:   The download speed.
        :rtype:     str * (float List) dict
        """
        return {field: [test.get_metric("bulkdownload") for test in self.get_field(field)]
                for field in self.get_fields()}
