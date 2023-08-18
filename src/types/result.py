# -*- coding: utf-8 -*-
# @Author: Ultraxime
# @Last Modified by:   Ultraxime
# @Last Modified time: 2023-08-18 16:26:07
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
Base classes for the results
"""
import os
import time
from abc import ABC
from abc import abstractmethod
from typing import Any
from typing import Dict
from typing import List
from typing import Optional

import matplotlib.pyplot as plt
import yaml

# pylint: disable=R0903
class Run(ABC):
    """
    This class describes a run.
    """
    _content: Any

    def __init__(self, content: Any):
        self._content = content

    @abstractmethod
    def get_metric(self, metric: str):
        """
        Gets the metric.

        :param      metric:  The metric
        :type       metric:  str
        """
        raise NotImplementedError


class Result(ABC):
    """
    This class describes the result of an experiment
    """
    _native: List[Run] | Dict[Any, Run]
    _masquerade: List[Run] | Dict[Any, Run]
    _squid: List[Run] | Dict[Any, Run]

    @abstractmethod
    def __init__(self, folder: str, name: str,
                 run_constructor: type,
                 _native: Optional[List | Dict] = None,
                 _masquerade: Optional[List | Dict] = None,
                 _squid: Optional[List | Dict] = None):
        assert issubclass(run_constructor, Run)
        if _native is not None and _masquerade is not None and _squid is not None:
            if isinstance(_native, list):
                self._native = [run_constructor(run) for run in _native]
                self._masquerade = [run_constructor(run) for run in _masquerade]
                self._squid = [run_constructor(run) for run in _squid]
                return
            if (isinstance(_native, dict) and isinstance(_masquerade, dict)
                and isinstance(_squid, dict)):
                self._native = {key: run_constructor(run) for key, run in _native.items()}
                self._masquerade = {key: run_constructor(run) for key, run in _masquerade.items()}
                self._squid = {key: run_constructor(run) for key, run in _squid.items()}
                return

        content = None
        for file in os.scandir(folder):
            if not file.is_dir() and name in file.name:
                with open(file.path, "r", encoding="utf-8") as file:
                    content = yaml.safe_load(file)

        if content is None:
            self._masquerade = []
            self._squid = []
            self._native = []
            return

        try:
            self._masquerade = [run_constructor(run) for run in content["proxy-masquerade"]]
        except KeyError:
            self._masquerade = []
        try:
            self._squid = [run_constructor(run) for run in content["proxy-squid"]]
        except KeyError:
            self._squid = []
        try:
            self._native = [run_constructor(run) for run in content["native"]]
        except KeyError:
            self._native = []

    def develop(self, field: List[Run] | Dict[Any, Run], convert) -> List:
        """
        Convert a set of test's results in one sorted list

        :param      field:    The field
        :type       field:    List[Run] | Dict[Any, Run]
        :param      convert:  The convert
        :type       convert:  Any -> List

        :returns:   the sorted list
        :rtype:     List
        """
        res = []
        for test in field:
            res.extend(convert(test))
        res.sort()
        return res


    def subplot(self, name: str, unit: str = "",
                convert = lambda x: [float(x)], scale: str = "linear"):
        """
        Create a subplot of the result

        :param      name:     The name
        :type       name:     str
        :param      unit:     The unit
        :type       unit:     str
        :param      convert:  The convert
        :type       convert:  Any -> List
        :param      scale:    The scale
        :type       scale:    str
        """
        mini = None
        maxi = None

        masquerade = self.develop(self._masquerade, convert)
        if masquerade:
            plt.plot(masquerade,
                     [(i+1)/len(masquerade) for i in range(len(masquerade))],
                     label=f"masquerade ({len(masquerade)} tests)")
            mini = masquerade[0]
            maxi = masquerade[-1]

        squid = self.develop(self._squid, convert)
        if squid:
            plt.plot(squid,
                     [(i+1)/len(squid) for i in range(len(squid))],
                     label=f"squid ({len(squid)} tests)")
            if mini and maxi:
                mini = min(mini, squid[0])
                maxi = max(maxi, squid[-1])
            else:
                mini = squid[0]
                maxi = squid[-1]

        native = self.develop(self._native, convert)
        if native:
            plt.plot(native,
                     [(i+1)/len(native) for i in range(len(native))],
                     label=f"native ({len(native)} tests)")
            if mini and maxi:
                mini = min(mini, native[0])
                maxi = max(maxi, native[-1])
            else:
                mini = native[0]
                maxi = native[-1]

        plt.axis([mini, maxi, 0, 1])
        plt.ylabel('ECDF')
        plt.xlabel(f'{name}' + (f" ({unit})" if unit != "" else ""))
        plt.xscale(scale)

        plt.legend(loc="lower right")

        plt.savefig(f'/results/results/{name} {time.asctime()}.png')
        plt.clf()

    def plot(self):
        """
        Create all the plot for the result
        """
        self.subplot(type(self).__name__)

    def get_field(self, field: str) -> List[Run] | Dict[Any, Run]:
        """
        Gets the field.

        :param      field:  The field
        :type       field:  str

        :returns:   The field.
        :rtype:     List
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

    def get_fields(self) -> List[str]:
        """
        Gets the fields.

        :returns:   The fields.
        :rtype:     str list
        """
        return ["native", "masquerade", "squid"]
