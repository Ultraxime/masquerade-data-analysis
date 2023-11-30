# -*- coding: utf-8 -*-
# @Author: Ultraxime
# @Last Modified by:   Ultraxime
# @Last Modified time: 2023-09-06 08:23:56
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
Module for the Data class
"""
from logging import debug
from logging import exception
from logging import info
from logging import warning
from os import mkdir
from typing import Callable
from typing import List
from typing import Mapping
from typing import Optional
from typing import Tuple
from typing import Union

import fastplot
from numpy import isnan
from numpy.typing import ArrayLike
from pandas import Series
from scipy.ndimage import median
from scipy.stats import mood
from scipy.stats import ttest_ind

from ..config import CONFIG
from .analyse_data import AnalysedData
from .analyse_data import AnalysedDataCountryDependent
from .analyse_data import AnalysedDataDependent
from .analyse_data import AnalysedDataWebsiteDependent
from .base_data import BaseData
from .base_data import BaseDataCountryDependent
from .base_data import BaseDataDependent
from .base_data import BaseDataWebsiteDependent


SCALES = ['linear']#,'log']
EXTENSIONS = ['pdf']#, 'png']
FONT_SIZE = 16


class Data(BaseData):
    """
    This class describes a set of data.
    """
    def analyse(self, test_type: str = 'all') -> AnalysedData:
        """
        Statistically analyse the data contained

        :param      test_type:   The test type
        :type       test_type:   str

        :returns:   The analysed data.
        :rtype:     AnalysedData

        :raises     ValueError:  if the specified test is not implemented
        """
        def aux(fct) -> Callable[[Series], Series]:
            def comp_value(obj1: ArrayLike, obj2: ArrayLike) -> Optional[Tuple[bool, float]]:
                try:
                    if not obj1 or not obj2:
                        return None
                    return (fct(obj1, obj2), (median(obj2) - median(obj1)) / median(obj1))
                except BaseException as err: # pylint: disable=W0718
                    info(f"While comparing the datas: {obj1} vs {obj2}, "
                         + f"the following occured:\n{err}")
                    tmp = -(median(obj1)-median(obj2))/median(obj1)
                    if isnan(tmp):
                        return None
                    return (False, tmp)
            def temp(line: Series) -> Series:
                if len(line) <= 1:
                    return Series([None], [None])
                res = []
                index = []
                for i in range(len(line)):
                    for j in range(i+1, len(line)):
                        res.append(comp_value(line.iloc[i], line.iloc[j]))
                        index.append(f"{line.index[i]} against {line.index[j]}")
                return Series(res, index)
            return temp
        def fct() -> Callable[[ArrayLike, ArrayLike], bool]:
            match test_type.lower():
                case "t-test":
                    # pylint: disable=C0301
                    return lambda a, b : abs(ttest_ind(a, b, equal_var=False).pvalue) <= 0.05   # pyright: ignore[reportGeneralTypeIssues]
                case "mood":
                    # pylint: disable=C0301
                    return lambda a, b : abs(mood(a, b).pvalue) <= 0.05                         # pyright: ignore[reportGeneralTypeIssues]
                case "all":
                    # pylint: disable=C0301
                    return lambda a, b : (abs(ttest_ind(a, b, equal_var=False).pvalue) <= 0.05  # pyright: ignore[reportGeneralTypeIssues]
                                          or abs(mood(a, b).pvalue) <= 0.05)                    # pyright: ignore[reportGeneralTypeIssues]
                case _:
                    raise ValueError(f"Unexpected test type: {test_type}")
        return AnalysedData(self.apply(aux(fct()), axis="columns"), interpreted=True)

    def plot(self, metric: str, depending: Union[List[str],str],
             conditions: str, aux: str = ""):
        """
        Plot the data using fastplot

        :param      metric:      The metric
        :type       metric:      str
        :param      depending:   The depending
        :type       depending:   str list | str
        :param      conditions:  The conditions
        :type       conditions:  str
        :param      aux:         The auxiliary
        :type       aux:         str

        :raises     ValueError:  wrong value for depending
        """
        if isinstance(depending, str):
            depending = [depending]
        depending = [x.lower() for x in depending]

        ylabel = (f"{CONFIG['metrics'][metric.lower()]['name']} "
                  + f"({CONFIG['metrics'][metric.lower()]['unit']})")

        xlabel = self.get_name()

        if aux:
            aux = f" ({aux})"

        folder = f"graphs/{str(xlabel).split(' ', maxsplit=1)[0]}"

        name = f"{folder}/{ylabel} depending on {xlabel} with {conditions}{aux}"
        if self.empty:
            warning(f"Issue while creating {name}, absence of datas")
            return
        self.fillna(inplace=True)

        info(f"{name} has on average {self.mean_length()} datapoints per box "
             + f"with a min of {self.min_length()} and max of {self.max_length()}.")

        try:
            mkdir("graphs")
        except FileExistsError:
            pass
        try:
            mkdir(folder)
        except FileExistsError:
            pass
        for scale in SCALES:
            for extension in EXTENSIONS:
                tmp_name = f"{name}({scale}).{extension}"
                try:
                    fastplot.plot(data=self, path=tmp_name.replace(' ', '_'), mode="boxplot_multi",
                                  xlabel=xlabel, ylabel=ylabel, yscale=scale,
                                  legend=True, legend_ncol=3, figsize=(8, 4),
                                  rcParams={'font.size': FONT_SIZE})
                                  # style='latex',
                                  # rcParams={'text.latex.preamble': r'\usepackage{libertine}'})
                    debug(f"Saved plot: {tmp_name}")
                except ValueError:
                    exception(f"Issue while creating {tmp_name}, check what it was:\n{self}")
                except TypeError:
                    exception(f"Issue while creating {tmp_name}, check what it was:\n{self}")

    def mean_length(self) -> float:
        """
        Get the average length of the list in the cells

        :returns:   The average length
        :rtype:     float
        """
        tmp_mean = self.applymap(len).mean()
        assert isinstance(tmp_mean, Series)
        new_mean = tmp_mean.mean()
        assert isinstance(new_mean, float)
        return new_mean

    def min_length(self) -> int:
        """
        Get the minimum length of the list in the cells

        :returns:   The minimum length
        :rtype:     int
        """
        return self.applymap(len).min().min()

    def max_length(self) -> int:
        """
        Get the maximum length of the list in the cells

        :returns:   The maximum length
        :rtype:     int
        """
        return self.applymap(len).max().max()

class DataDependent(Data, BaseDataDependent):
    """
    This class describes a data depending on something.
    """
    _analysed_type: type = AnalysedDataDependent

    def __init__(self, data: Optional[Mapping[str, Data]] = None):
        super().__init__(data)

    def analyse(self, test_type: str = "all") -> AnalysedDataDependent:
        """
        Statistically analyse country depending data

        :param      test_type:  The test type
        :type       test_type:  str

        :returns:   The analysed data .
        :rtype:     AnalysedDataDependent
        """
        return self._analysed_type(
            {key: data.analyse(test_type) for key, data in self.items()})

    def plot(self, metric: str, depending: Union[List[str],str],
             conditions: str, aux: str = ""):
        for key, data in self.items():
            if aux:
                aux_tmp = f"{aux} {key}"
            else:
                aux_tmp = key
            data.plot(metric, depending, conditions, aux_tmp)

class DataCountryDependent(BaseDataCountryDependent, DataDependent):
    """
    This class describes a data country dependent.
    """
    _analysed_type: type = AnalysedDataCountryDependent


class DataWebsiteDependent(BaseDataWebsiteDependent, DataDependent):
    """
    This class describes a data website depending.
    """
    _analysed_type: type = AnalysedDataWebsiteDependent
