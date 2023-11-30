# -*- coding: utf-8 -*-
# @Author: Ultraxime
# @Last Modified by:   Ultraxime
# @Last Modified time: 2023-08-25 14:19:33
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
Module for the base class for the Data classes
"""
from __future__ import annotations

from collections.abc import Mapping
from typing import Any
from typing import Hashable
from typing import Optional

from numpy import isnan
from pandas import DataFrame
from typing_extensions import Self


class BaseData(DataFrame):
    """
    This class describes the base data that will be inherit by other class
    """
    _metadata = ["_default_value"]
    _default_value: Any

    def __init__(self, data = None, default = None, **kwargs):
        super().__init__(data, **kwargs)
        super().sort_index(inplace=True)
        if isinstance(data, DataFrame):
            self.set_name(data.columns.name)
        if default:
            self._default_value = default.copy()
        else:
            self._default_value = []
        self.fillna(inplace=True)

    def set_name(self, name: Hashable):
        """
        Sets the name.

        :param      name:  The name
        :type       name:  Hashable
        """
        self.columns.name = name

    def get_name(self) -> Optional[str]:
        """
        Gets the name.

        :returns:   The name.
        :rtype:     str
        """
        if self.columns.name is None:
            return None
        return str(self.columns.name)

    # pylint: disable=R0913
    def apply(self, func, axis=0, raw=False, result_type=None, args=(), **kwargs) -> Self:
        tmp = type(self)(super().apply(func, axis, raw, result_type, args, **kwargs))
        tmp.set_name(self.get_name())
        if tmp.isna().values.any():
            tmp = tmp.fillna()
        assert isinstance(tmp, type(self))
        return tmp

    def applymap(self, func, na_action=None, **kwargs) -> Self:
        tmp = type(self)(super().applymap(func, na_action, **kwargs))
        tmp.set_name(self.get_name())
        if tmp.isna().values.any():
            tmp = tmp.fillna()
        assert isinstance(tmp, type(self))
        return tmp

    def sort_index(self, **kwargs) -> Self:
        return type(self)(super().sort_index(**kwargs))

    def transpose(self, *args, copy=False) -> Self:
        return type(self)(super().transpose(*args, copy=copy)).sort_index()

    # pylint: disable=W1113        # Not my signature choice
    def fillna(self, value: Any = None, *args, method=None, axis=None,
               inplace=False, limit=None, downcast=None) -> Optional[Self]:
        if not self.isna().values.any():
            if inplace:
                return None
            return self
        if value is None:
            value = self._default_value
        if isinstance(value, list):
            def aux(cell):
                try:
                    if cell is None or isnan(cell):
                        return value.copy()
                    return cell
                except TypeError:
                    return cell
                except ValueError:
                    return cell
            if inplace:
                for column in self:
                    self[column] = self[column].apply(aux)
                return None
            return self.applymap(aux)
        return type(self)(super().fillna(value, *args, method=method, axis=axis,
                                         inplace=inplace, limit=limit, downcast=downcast))


class BaseDataDependent(dict, BaseData):
    """
    This class describes a base data dependent on something.
    """
    def __init__(self, datas: Optional[Mapping[str, BaseData]] = None):
        super().__init__()
        if datas is None:
            datas = {}
        for key, data in datas.items():
            if data is not None and not data.empty:
                self[key] = data

    def __str__(self, **kwargs) -> str:
        string = ""
        for key, data in self.items():
            string += f"{key}\n"
            string += f"{data}\n"
        return string

    def set_name(self, name: Hashable):
        for key in self:
            self[key].set_name(name)

    def get_name(self) -> Hashable:
        name = None
        for key in self:
            if self[key].get_name() is not None:
                name = self[key].get_name()
        if name is not None:
            self.set_name(name)
        return name

    # pylint: disable=R0913     # I can't choose the number of arguments
    def apply(self, func, axis=0, raw=False, result_type=None, args=(), **kwargs) -> Self:
        return type(self)({key: data.apply(func, axis, raw, result_type, args, **kwargs)
                           for key, data in self.items()})

    def applymap(self,func, na_action=None, **kwargs) -> Self:
        return type(self)({key: data.applymap(func, na_action, **kwargs).fillna(self._default)
                           for key, data in self.items()})

    def transpose(self, *args, copy=False) -> Self:
        return type(self)({key: data.transpose(*args, copy=False) for key, data in self.items()})

    def sort_index(self, **kwargs) -> Self:
        return type(self)({key: data.sort_index(**kwargs) for key, data in self.items()})


class BaseDataCountryDependent(BaseDataDependent):
    """
    This class describes a base data country dependent.
    """


class BaseDataWebsiteDependent(BaseDataDependent):
    """
    This class describes a base data website dependent.
    """
