# -*- coding: utf-8 -*-
# @Author: Ultraxime
# @Last Modified by:   Ultraxime
# @Last Modified time: 2023-08-18 18:01:13
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
Module for the AnalysedData class
"""
from collections.abc import Mapping
from logging import warning
from typing import Hashable
from typing import List
from typing import Optional
from typing import Tuple

from numpy import isnan
from pandas import Series
from typing_extensions import Self

from .base_data import BaseData
from .base_data import BaseDataCountryDependent
from .base_data import BaseDataDependent
from .base_data import BaseDataWebsiteDependent


class AnalysedData(BaseData):
    """
    This class describes an analysed data.
    """
    def __init__(self, data: Optional[BaseData] = None, default: Optional[List] = None,
                 interpreted: bool = False, **kwargs):
        if data is None:
            data = BaseData()
        if default is None:
            default = [None, None, None]
        def interpret(line: Series) -> Series:
            res: List[Optional[Tuple]] = default.copy()
            for i, value in enumerate(line):
                if value:
                    test, err = value
                    if not isnan(err):
                        match line.index[i]:
                            case "native against squid" | "it against de":
                                res[0] = (test, err)
                            case "squid against native" | "de against it":
                                res[0] = (test, 1 - (1 / (1 - err)) )
                            case "native against masquerade" | "it against fr":
                                res[1] = (test, err)
                            case "masquerade against native" | "fr against it":
                                res[1] = (test, 1 - (1 / (1 - err)) )
                            case "squid against masquerade" | "de against fr":
                                res[2] = (test, err)
                            case "masquerade against squid" | "fr against de":
                                res[2] = (test, 1 - (1 / (1 - err)) )
                            case None:
                                pass
                            case name:
                                warning(f"Unexpected column name: {name}")
                    else:
                        warning(f"Found nan in column: {line.index[i]}")
            return Series([res])
        if interpreted:
            super().__init__(data.apply(interpret, axis="columns"), default, **kwargs)
        else:
            super().__init__(data, default, **kwargs)

    def __str__(self, unit: Optional[str] = None) -> str:
        def replace(cell):
            # pylint: disable=C0103
            up = "$\\nearrow$"
            down = "$\\searrow$"
            res = ""
            for value in cell:
                match value:
                    case None:
                        res += " & "
                    case (test, err):
                        content = up if err > 0 else (down if err < 0 else "=")
                        if test:
                            res += f"\\cellcolor{{green}}{content} & "
                        else:
                            # if err < 0.05 and err > -0.05:
                            #     content = "="
                            # else:
                            res += f"\\cellcolor{{red}}{content} & "
                    case _:
                        raise ValueError(f"Unexpected: {value}")
            res = res[:-3]
            return res
        styler = self.applymap(replace).style
        newline = "\\\\"
        styler.format_index(
            lambda name: f"\\multicolumn{{3}}{{c}}{{\\makecell{{{name.replace(' ', newline)}}}}}",
            axis="columns")
        if unit is not None:
            styler.format_index(lambda index: f"{index} ({unit})", axis='index')
        res = styler.to_latex(hrules=True)
        if isinstance(res, str):
            return res.replace('%', '\\%')
        return ""

    # pylint: disable=W0221         # issue with importing the right thing for the last arg
    def insert(self, loc: int, column: Hashable, value: Self, **kwargs):
        if loc == -1:
            loc = len(self.columns)
        assert value.shape[1] == 1
        if self.get_name() is None and value.get_name() is not None:
            self.set_name(value.get_name())
        super().insert(loc, column, value[0], **kwargs)
        self.fillna(self._default_value, inplace=True)


class AnalysedDataDependent(BaseDataDependent, AnalysedData):
    """
    This class describes an analysed data depending on something.
    """
    def __init__(self, data: Optional[Mapping[str, AnalysedData]] = None):
        super().__init__(data)

    # pylint: disable=W0221         # issue with importing the right thing for the last arg
    def insert(self, loc: int, column: Hashable, value: Self, **kwargs):
        for key in value:
            if key not in self:
                self[key] = AnalysedData()
        for key in self:
            if key in value:
                self[key].insert(loc, column, value[key], **kwargs)


class AnalysedDataCountryDependent(BaseDataCountryDependent, AnalysedDataDependent):
    """
    This class describes an analysed data country dependent.
    """


class AnalysedDataWebsiteDependent(BaseDataWebsiteDependent, AnalysedDataDependent):
    """
    This class describes an analysed data website depending.
    """
