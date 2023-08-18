# -*- coding: utf-8 -*-
# @Author: Ultraxime
# @Last Modified by:   Ultraxime
# @Last Modified time: 2023-08-18 14:59:27
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
Module for the speed test result
"""
from typing import Dict
from typing import List

from .result import Result
from .result import Run


# pylint: disable=R0903
class SpeedTestRun(Run):
    """
    This class describes a speed test run.
    """
    def get_metric(self, metric: str):
        match metric.lower():
            case "ping":
                res = int(self._content["ping_ms"])
            case "download":
                res = float(self._content["download_mbps"])
            case "upload":
                res = float(self._content["upload_mbps"])
            case _:
                raise ValueError
        if res == 0:
            return "NULL"
        return res


class SpeedTest(Result):
    """
    This class describes a speed test's result.
    """
    def __init__(self, folder: str = ".", name: str = "speedtest",
                 run_constructor=SpeedTestRun, **kwargs):
        super().__init__(folder, name, run_constructor, **kwargs)

    def plot(self):
        self.subplot("ping", "ms", lambda x : [int(x["ping_ms"])])
        self.subplot("download", "mbps", lambda x : [float(x["download_mbps"])])
        self.subplot("upload", "mbps", lambda x : [float(x["upload_mbps"])])

    def get_ping(self) -> Dict[str, List[int]]:
        """
        Gets the ping.

        :returns:   The ping.
        :rtype:     str * (int List) dict
        """
        return {field: [test.get_metric("ping") for test in self.get_field(field)]
                for field in self.get_fields()}

    def get_download(self) -> Dict[str, List[float]]:
        """
        Gets the download.

        :returns:   The download speed.
        :rtype:     str * (float List) dict
        """
        return {field: [test.get_metric("download") for test in self.get_field(field)]
                for field in self.get_fields()}

    def get_upload(self) -> Dict[str, List[float]]:
        """
        Gets the upload.

        :returns:   The upload speed.
        :rtype:     str * (float List) dict
        """
        return {field: [test.get_metric("upload") for test in self.get_field(field)]
                for field in self.get_fields()}
