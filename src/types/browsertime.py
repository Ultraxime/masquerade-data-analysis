# -*- coding: utf-8 -*-
# @Author: Ultraxime
# @Last Modified by:   Ultraxime
# @Last Modified time: 2023-08-21 10:40:37
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
Module for the browsertime results
"""
import json
import os
import time
from typing import Dict
from typing import List
from typing import Optional

import yaml

from .result import Result
from .result import Run


class Report(Run):
    """
    This class describes the result of one run of browsertime.
    """
    _page_load_time: List[int]
    _speed_index: List[int]

    def __init__(self, old_self = None,
                 filename: str = "",
                 _page_load_time: Optional[List] = None,
                 _speed_index: Optional[List] = None):
        super().__init__(None)
        if old_self:
            self._page_load_time = old_self._page_load_time
            self._speed_index = old_self._speed_index
            return
        if _page_load_time is not None and _speed_index is not None:
            self._page_load_time = _page_load_time
            self._speed_index = _speed_index
            return

        self._page_load_time = []
        self._speed_index = []

        try:
            with open(filename+"/browsertime.json", "r", encoding="utf-8") as file:
                content = json.load(file)

            for attempt in content[0]["browserScripts"]:
                self._page_load_time.append(attempt["timings"]["pageTimings"]["pageLoadTime"])
            for attempt in content[0]["visualMetrics"]:
                self._speed_index.append(attempt["SpeedIndex"])
        except FileNotFoundError:
            pass

    def get_page_load_time(self) -> List[int]:
        """
        Gets the page load time.

        :returns:   The page load time.
        :rtype:     int list
        """
        return self._page_load_time

    def get_speed_index(self) -> List[int]:
        """
        Gets the speed index.

        :returns:   The speed index.
        :rtype:     int list
        """
        return self._speed_index

    def get_metric(self, metric: str):
        match metric.lower():
            case "plt":
                return [plt for plt in self.get_page_load_time() if plt != 0]
            case "si":
                return [si for si in self.get_speed_index() if si != 0]
            case _:
                raise ValueError





class BrowserTime(Result):
    """
    This class describes the result of one run of the browsertime experiment.
    """
    _native: Dict[str, Report]
    _masquerade: Dict[str, Report]
    _squid: Dict[str, Report]

    def __init__(self, folder: str = ".", run_constructor=Report,
                 _native: Optional[Dict] = None,
                 _masquerade: Optional[Dict] = None,
                 _squid: Optional[Dict] = None):
        if _native is not None and _masquerade is not None and _squid is not None:
            # pylint: disable=C0301
            super().__init__(folder, "", run_constructor, _native=_native, _masquerade=_masquerade, _squid=_squid) # pyright: ignore[reportGeneralTypeIssues]
            return

        self._native = {}
        self._masquerade = {}
        self._squid = {}

        for website in os.scandir(folder):
            if website.name not in ("archives", "results") and website.is_dir():
                attempts = list(os.scandir(website.path))
                if len(attempts) == 3:
                    attempts.sort(key=lambda f: f.path)
                    self._native[website.name] = run_constructor(filename=attempts[0].path)
                    self._masquerade[website.name] = run_constructor(filename=attempts[1].path)
                    self._squid[website.name] = run_constructor(filename=attempts[2].path)

    def save(self):
        """
        Save the object as a yaml file
        """
        with open(f'/results/results/browsertime {time.asctime()}.yml',
                  "w", encoding="utf-8") as file:
            yaml.dump(self, file)

    def get_page_load_time(self) -> Dict[str, List[int]]:
        """
        Gets the page load time.

        :returns:   The page load time.
        :rtype:     str * (int List) dict
        """
        res = {"native": [],
               "masquerade" : [],
               "squid": []}
        for website, native in self._native.items():
            if website in self._masquerade and website in self._squid:
                count = min(len(native.get_page_load_time()),
                            len(self._masquerade[website].get_page_load_time()),
                            len(self._squid[website].get_page_load_time()))
                res["native"].extend(native.get_page_load_time()[:count])
                res["masquerade"].extend(self._masquerade[website].get_page_load_time()[:count])
                res["squid"].extend(self._squid[website].get_page_load_time()[:count])
        return res

    def get_speed_index(self) -> Dict[str, List[int]]:
        """
        Gets the speed index.

        :returns:   The speed index.
        :rtype:     str * (int List) dict
        """
        res = {"native": [],
               "masquerade" : [],
               "squid": []}
        for website, native in self._native.items():
            if website in self._masquerade and website in self._squid:
                count = min(len(native.get_speed_index()),
                            len(self._masquerade[website].get_speed_index()),
                            len(self._squid[website].get_speed_index()))
                res["native"].extend(native.get_speed_index()[:count])
                res["masquerade"].extend(self._masquerade[website].get_speed_index()[:count])
                res["squid"].extend(self._squid[website].get_speed_index()[:count])
        return res
