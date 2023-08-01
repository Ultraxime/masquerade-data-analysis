"""
Module for the browsertime results
"""

import json
import os
import time

from typing import List, Dict, Optional

import yaml


class Report:
    """
    This class describes the result of one run of browsertime.
    """
    _page_load_time: List[int]
    _speed_index: List[int]

    def __init__(self, filename: str = "",
                 _page_load_time: Optional[List] = None,
                 _speed_index: Optional[List] = None):
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


class BrowserTime:
    """
    This class describes the result of one run of the browsertime experiment.
    """
    _native: Dict[str, Report]
    _masquerade: Dict[str, Report]
    _squid: Dict[str, Report]

    def __init__(self, folder: str = ".",
                 _native: Optional[Dict] = None,
                 _masquerade: Optional[Dict] = None,
                 _squid: Optional[Dict] = None):
        if _native is not None and _masquerade is not None and _squid is not None:
            self._native = _native
            self._masquerade = _masquerade
            self._squid = _squid
            return

        self._native = {}
        self._masquerade = {}
        self._squid = {}

        for website in os.scandir(folder):
            if website.name not in ("archives", "results") and website.is_dir():
                attempts = list(os.scandir(website.path))
                assert len(attempts) == 3
                attempts.sort(key=lambda f: f.path)
                self._native[website.name] = Report(attempts[0].path)
                self._masquerade[website.name] = Report(attempts[1].path)
                self._squid[website.name] = Report(attempts[2].path)

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

    def get_field(self, field: str) -> Dict[str, Report]:
        """
        Gets the field.
        
        :param      field:  The field
        :type       field:  str
        
        :returns:   The field.
        :rtype:     Dict[str, Report]
        """
        match field:
            case "native":
                return self._native
            case "masquerade":
                return self._masquerade
            case "squid":
                return self._squid
            case _:
                raise ValueError
