# -*- coding: utf-8 -*-
# @Author: Ultraxime
# @Last Modified by:   Ultraxime
# @Last Modified time: 2023-08-18 18:34:23
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
Module for the results class
"""
from logging import debug
from logging import info
from os import scandir
from posix import DirEntry
from sqlite3 import connect
from sqlite3 import Connection
from sqlite3 import Cursor
from sqlite3 import OperationalError
from typing import Dict
from typing import Iterable
from typing import List
from typing import Tuple
from typing import Union

import yaml

from .config import CONFIG
from .datas import AnalysedData
from .datas import AnalysedDataCountryDependent
from .datas import Data
from .datas import DataCountryDependent
from .datas import DataWebsiteDependent
from .loader import Loader
from .types import Connectivity
from .types import Result
from .types import Run

class Results:
    """
    This class describes the results of several experiments.
    """
    _connection: Connection
    _cursor: Cursor

    def __init__(self, folder: str = "datas", database: str = "tmp"):
        if database[-3:] != ".db":
            database += ".db"

        info("Creating the database")
        self._connection = connect(database)
        self._cursor = self._connection.cursor()

        try:
            self._cursor.execute("""CREATE TABLE conditions(
                                    id INTEGER PRIMARY KEY NOT NULL,
                                    upload INTEGER,
                                    download INTEGER,
                                    rtt INTEGER,
                                    loss INTEGER,
                                    technology TEXT,
                                    quality TEXT,
                                    operator TEXT,
                                    country TEXT
                                )""")
        except OperationalError:
            pass

        try:
            self._cursor.execute("""CREATE TABLE experiments(
                                    id INTEGER PRIMARY KEY NOT NULL,
                                    country char(2) NOT NULL,
                                    run INTEGER NOT NULL,
                                    condition INTEGER NOT NULL,
                                    date REAL NOT NULL,
                                    FOREIGN KEY(condition) REFERENCES conditions(id)
                                )""")
        except OperationalError:
            pass

        for table, conf in CONFIG["tables"].items():
            columns = [f"{name} {typ}" for name, typ in conf["columns"].items()]
            if conf["website_dependent"]:
                columns.append("website TEXT NOT NULL")
            request = f"""CREATE TABLE {table}(
                          experimentid INTEGER,
                          proxy TEXT NOT NULL,
                          {",".join(columns)},
                          FOREIGN KEY(experimentid) REFERENCES experiments(id))"""
            try:
                self._cursor.execute(request)
            except OperationalError:
                pass

        for country in scandir(folder):
            if country.is_dir():
                for run in scandir(country.path):
                    if run.is_dir():
                        self._add_run(run, country.name)
        info("Finished Creating the database")

    def _add_run(self, run: DirEntry, country: str):
        debug(f"Adding run {int(run.name)} of {country} in the database")
        dates = self._select(f"""SELECT date FROM experiments
                                 WHERE country=\"{country}\"
                                    AND run={int(run.name)}""")
        new_date = run.stat().st_mtime
        modified = not dates
        for date in dates:
            if date < new_date:
                modified = True

        if modified:
            for table in CONFIG["tables"]:
                self._cursor.execute(f"""DELETE FROM {table}
                                         WHERE experimentid IN (SELECT id FROM experiments
                                                                WHERE country=\"{country}\"
                                                                    AND run={int(run.name)})""")
            self._cursor.execute(f"""DELETE FROM experiments
                                     WHERE country=\"{country}\" AND run={int(run.name)}""")
            for experiment in scandir(run.path):
                if ".yml" in experiment.name:
                    debug(f"Adding experiment {experiment.name}")
                    self._add_experiment(experiment, country, int(run.name), new_date)
                else:
                    debug(f"Ignoring file {experiment.name}, not a yaml file")
        else:
            debug(f"Ignoring run {int(run.name)} of {country}, already in the database")

    def _add_experiment(self, experiment: DirEntry, country: str, run: int, date: float):
        condition = self._add_conditon(experiment.name)
        experiment_id = self._select(f"""INSERT INTO experiments (country, run, condition, date)
                                                 VALUES (\"{country}\", {run}, {condition}, {date})
                                                 RETURNING id""")
        assert len(experiment_id) == 1
        assert isinstance(experiment_id[0], int)

        with open(experiment.path, 'r', encoding='utf-8') as file:
            data = yaml.load(file.read(), Loader=Loader)

        for table in CONFIG["tables"]:
            self._insert(data[table], table, experiment_id[0])

        self._connection.commit()

    def _add_conditon(self, values: str) -> int:
        data = values.split(" ")
        try:
            upload = int(data[0])//1000
            download = int(data[1])//1000
            rtt = int(data[2])
            loss = int(data[3])
            condition = self._select(f"""SELECT id FROM conditions
                                                WHERE upload={upload}
                                                    AND download={download}
                                                    AND rtt={rtt}
                                                    AND loss={loss}""")
            if not condition:
                condition = self._select(f"""INSERT INTO conditions (upload, download,
                                                                            rtt, loss)
                                                    VALUES ({upload}, {download}, {rtt}, {loss})
                                                    RETURNING id""")
        except ValueError:
            technology = data[0]
            quality = data[1]
            _country = data[2]
            operator = data[3]

            # Ignore operator, not needed at the time
            if operator != "universal":
                operator = "universal"
            condition = self._select(f"""SELECT id FROM conditions
                                                WHERE technology=\"{technology}\"
                                                    AND quality=\"{quality}\"
                                                    AND operator=\"{operator}\"
                                                    AND country=\"{_country}\"""")
            if not condition:
                condition = self._select(f"""INSERT INTO conditions (technology, quality,
                                                                            operator, country)
                                                    VALUES (\"{technology}\",\"{quality}\",
                                                            \"{operator}\", \"{_country}\")
                                                    RETURNING id""")
        assert len(condition) == 1
        assert isinstance(condition[0], int)
        return condition[0]

    def _select(self, request: str) -> List:
        try:
            res = []
            for line in self._cursor.execute(request).fetchall():
                if line is not None:
                    if len(line) == 1:
                        if line[0] is not None:
                            res.append(line[0])
                    else:
                        res.append([value for value in line if value is not None])
            return res
        except OperationalError:
            debug(f"An error occured while executing this resquest: {request}")
            raise

    def _insert(self, data: Result, table:str, experiment_id: int):
        def aux(metrics: list, values: list, test: Run, table: str):
            constant_field = len(metrics)
            for metric, data in CONFIG["metrics"].items():
                if data["table"] == table:
                    metrics.append(data["column"])
                    if CONFIG["tables"][table]["columns"][metrics[-1]] == "TEXT":
                        values.append(f"\"{test.get_metric(metric)}\"")
                    else:
                        values.append(test.get_metric(metric))
            if (isinstance(values[constant_field], Iterable)
                and not isinstance(values[constant_field], str)):
                maxi = max(len(metric) for metric in values[constant_field:])
                for metric in values[constant_field:]:
                    metric.extend(["NULL"]*(maxi - len(metric)))
                for i in range(maxi):
                    val = (values[:constant_field]
                           + [str(metric[i]) for metric in values[constant_field:]])
                    if any(v!= 'NULL' for v in val[constant_field:]):
                        self._cursor.execute(f"""INSERT INTO {table} ({", ".join(metrics)})
                                                 VALUES ({", ".join(val)})""")
            else:
                if any(v!= 'NULL' for v in values[constant_field:]):
                    self._cursor.execute(f"""INSERT INTO {table} ({", ".join(metrics)})
                                             VALUES ({", ".join([str(val) for val in values])})""")
        for field in data.get_fields():
            if CONFIG["tables"][table]["website_dependent"]:
                field_data = data.get_field(field)
                assert isinstance(field_data, dict)
                for website, test in field_data.items():
                    metrics = ["experimentid", "proxy", "website"]
                    values = [str(experiment_id), f"\"{field}\"", f"\"{website}\""]
                    aux(metrics, values, test, table)
            else:
                for test in data.get_field(field):
                    metrics = ["experimentid", "proxy"]
                    values = [str(experiment_id), f"\"{field}\""]
                    aux(metrics, values, test, table)

    # pylint: disable=R1702
    def plot(self, full: bool = False,
             country_dependent: bool = False, website_dependent: bool = False):
        """
        Plot all the metrics for all the scenarii

        :param      full:               If we want a full or only specific plot
        :type       full:               bool
        :param      country_dependent:  If it is not a full does we want the country dependent plot
        :type       country_dependent:  bool
        :param      website_dependent:  If it is not a full does we want the website dependent plot
        :type       website_dependent:  bool
        """
        for depending in ['rtt', 'loss', ['upload', 'download'], ['technology', 'quality']]:
            info(f"Plotting depending on: {depending}")
            if full:
                for country_dep in [True, False]:
                    for metric in CONFIG['metrics']:
                        info(f"Plotting: {CONFIG['metrics'][metric]['name']}")
                        if CONFIG["tables"][CONFIG['metrics'][metric]['table']
                                           ]['website_dependent']:
                            for website_dep in [True, False]:
                                self.plot_metric(metric, depending, country_dep, website_dep)
                        else:
                            self.plot_metric(metric, depending, country_dep)
            else:
                for metric in CONFIG['metrics']:
                    info(f"Plotting: {CONFIG['metrics'][metric]['name']}")
                    self.plot_metric(metric, depending, country_dependent, website_dependent)

    def print_analyse(self, country_dependent: bool = False, **kwargs) -> Dict[str, str]:
        """
        Create the dict string corresponding to the analyse.

        :param      country_dependent:  The country dependent
        :type       country_dependent:  bool
        :param      kwargs:             The keywords arguments
        :type       kwargs:             dictionary

        :returns:   A dict of conditions and analyse results
        :rtype:     Dict str * str
        """
        res = {}
        value, conditions = self.analyse(country_dependent, **kwargs)
        for depending, datas in value.items():
            res[f"{depending} with {conditions[depending]}"] = str(datas)
        return res


    def analyse(self, country_dependent: bool = False, test_type: str = "all"
                    ) -> Tuple[Dict[str, AnalysedData], Dict[str, str]]:
        """
        Compare the different scenarios

        :param      country_dependent:  The country dependent
        :type       country_dependent:  bool
        :param      test_type:          The test type
        :type       test_type:          str

        :returns:   A dict of the analysed data with the coresponding conditions
        :rtype:     Dict (str * AnalysedData) * Dict(str * str)
        """
        res = {}
        conditions = {}
        for depending in ['rtt', 'loss', ['upload', 'download'], ['technology', 'quality']]:
            info(f"Analysing depending on: {depending}")
            if country_dependent:
                res[str(depending)] = AnalysedDataCountryDependent()
            else:
                res[str(depending)] = AnalysedData()
            for metric in CONFIG['metrics']:
                info(f"Analysing: {CONFIG['metrics'][metric]['name']}")
                datas, conditions[str(depending)] = self.analyse_metric(metric,
                                                                        depending,
                                                                        country_dependent,
                                                                        test_type)
                res[str(depending)].insert(-1, CONFIG["metrics"][metric]["name_short"], datas)
        return res, conditions


    def analyse_metric(self, metric: str, depending: Union[List[str],str],
                       country_dependent: bool = False, test_type: str = "t-test"
                      ) -> Tuple[AnalysedData, str]:
        """
        Analyse a metric

        :param      metric:             The metric
        :type       metric:             str
        :param      depending:          The depending
        :type       depending:          str list | str
        :param      country_dependent:  If it is country dependent
        :type       country_dependent:  bool
        :param      test_type:          The test type
        :type       test_type:          str

        :returns:   The analysed datas and the condition
        :rtype:     AnalysedData * str
        """
        datas, conditions = self.get_metric(metric, depending, country_dependent)
        return datas.analyse(test_type), conditions

    def get_metric(self, metric: str, depending: Union[List[str],str],
                   country_dependent: bool = False, website_dependent: bool = False
                   ) -> Tuple[Data, str]:
        """
        Get the Datas(s) corresponding to the metrics

        :param      metric:             The metric
        :type       metric:             str
        :param      depending:          The depending
        :type       depending:          str list | str
        :param      country_dependent:  The country dependent
        :type       country_dependent:  bool
        :param      website_dependent:  The website dependent
        :type       website_dependent:  bool

        :returns:   The metric.
        :rtype:     Data | dict (str * Data) * str

        :raises     AssertionError:     Wrong usage of the method
        """
        experiments, conditions = self.get_experiment(depending, country_dependent)
        if isinstance(depending, str):
            depending = [depending]
        depending = [x.lower() for x in depending]
        match depending:
            case ['rtt']:
                name = "RTT (ms)"
            case ['loss']:
                name = "Loss (%)"
            case ['upload' , 'download'] | ['download', 'upload']:
                name = "Bandwidth (Mbps)"
            case ['technology', 'quality']:
                name = "Network"
            case _:
                raise ValueError(f'Unknown depending: {depending}')
        if country_dependent:
            ret = DataCountryDependent()
            for country, ids in experiments.items():
                assert isinstance(ids, dict)
                data = self.get_data(ids, metric, website_dependent)
                data.set_name(name)
                assert isinstance(country, str)
                ret[country] = data
            return ret, conditions
        # pylint: disable=C0301
        data = self.get_data(experiments, metric, website_dependent)    # pyright: ignore[reportGeneralTypeIssues]
        data.set_name(name)
        return data, conditions

    def plot_metric(self, metric: str, depending: Union[List[str],str],
                    country_dependent: bool = False, website_dependent: bool = False):
        """
        Plot the graph(s) corresponding to the metrics

        :param      metric:             The metric
        :type       metric:             str
        :param      depending:          The depending
        :type       depending:          str list | str
        :param      country_dependent:  The country dependent
        :type       country_dependent:  bool
        :param      website_dependent:  The website dependent
        :type       website_dependent:  bool

        :raises     AssertionError:     Wrong usage of the method
        """
        data, conditions = self.get_metric(metric, depending, country_dependent, website_dependent)
        data.plot(metric, depending, conditions)

    # pylint: disable=R0912
    def get_data(self, experiments: Dict[int,List[int]],
                 metric: str, website_dependent: bool = False
                ) -> Data | DataWebsiteDependent:
        """
        Gets the data.

        :param      experiments:        The experiments
        :type       experiments:        dict int * int list
        :param      metric:             The metric
        :type       metric:             str
        :param      website_dependent:  The website dependent
        :type       website_dependent:  bool

        :returns:   The data.
        :rtype:     dict str * (dict int * (list)) | (dict int * (list))

        :raises     ValueError:         Wrong parameters
        """
        metric = metric.lower()
        table = CONFIG["metrics"][metric]["table"]

        column = CONFIG["metrics"][metric]["column"]

        proxies = self._select(f"SELECT DISTINCT(proxy) FROM {table}")

        data = {}

        if not CONFIG["tables"][table]["website_dependent"]:

            for condition, ids in experiments.items():
                request = f"""SELECT {column} FROM {table}
                              WHERE proxy=\"%s\"
                                AND experimentid {f'= {ids[0]}' if len(ids) == 1
                                                  else f'IN {tuple(ids)}'}"""
                data[condition] = {}
                for proxy in proxies:
                    data[condition][proxy] = self._select(request % proxy)
                    if data[condition][proxy] == []:
                        del data[condition][proxy]
                if "masquerade" not in data[condition] or "native" not in data[condition]:
                    del data[condition]
                else:
                    mini = min(len(value) for _, value in data[condition].items())
                    if mini == 0:
                        del data[condition]
                    else:
                        for proxy in data[condition]:
                            data[condition][proxy] = data[condition][proxy][:mini]
            return Data(data).transpose()

        for website in self._select(f"SELECT DISTINCT(website) FROM {table}"):
            data[website] = {}
            mini = None
            for condition, ids in experiments.items():
                request = f"""SELECT {column} FROM {table}
                                  WHERE proxy=\"%s\" AND website=\"{website}\"
                                        AND {column} IS NOT NULL
                                        AND experimentid {f'= {ids[0]}' if len(ids) == 1
                                                          else f'IN {tuple(ids)}'}"""
                data[website][condition] = {}
                for proxy in proxies:
                    data[website][condition][proxy] = self._select(request % proxy)
                    mini = (len(data[website][condition][proxy]) if mini is None
                            else min(mini, len(data[website][condition][proxy])))
            # Strengthening the datas,
            # to be sure that a website is counted the same number of time for every situation
            if mini == 0:
                debug(f"Discarded website: {website} with data: {data[website]}")
                del data[website]
            else:
                for condition in experiments:
                    for proxy in proxies:
                        data[website][condition][proxy] = data[website][condition][proxy][:mini]

        if website_dependent:
            return DataWebsiteDependent({website: Data(value) for website, value in data.items()}
                ).transpose()
        ret = {}
        for condition in experiments:
            ret[condition] = {}
            for proxy in proxies:
                ret[condition][proxy] = []
                for _, website in data.items():
                    ret[condition][proxy].extend(website[condition][proxy])
        return Data(ret).transpose()

    # pylint: disable=R0912,R0914
    def get_experiment(self, depending: Union[List[str],str], country_dependent: bool = False
        ) -> Tuple[Union[Dict[str,Dict[int,List[int]]], Dict[int,List[int]]], str]:
        """
        Gets the experiments corresponding to the depending variable variating
            and the others being still.

        :param      depending:          The depending
        :type       depending:          str list | str
        :param      country_dependent:  The country dependent
        :type       country_dependent:  bool

        :returns:   The experiment.
        :rtype:     (dict str * (dict int * (int list)) | (dict int * (int list))) * str

        :raises     AssertionError:     Appends if the database is badly constructed
        :raises     ValueError:         Wrong parameters
        """

        if isinstance(depending, str):
            depending = [depending]
        depending = [x.lower() for x in depending]
        match depending[0]:
            case "upload" | "download" | "rtt" | "loss":
                condition_str = ("technology IS NULL AND quality IS NULL "
                                 + "AND country IS NULL and operator IS NULL")
                group_by = ["upload", "download", "rtt", "loss"]
            case "technology" | "quality" | "country" | "operator":
                condition_str = ("upload IS NULL AND download IS NULL "
                                 + "AND rtt IS NULL and loss IS NULL")
                group_by = ["technology", "quality", "country", "operator"]
            case _:
                raise ValueError(f"Unknown depending: {depending[0]}")
        for column in depending:
            group_by.remove(column)


        request = f"""SELECT {','.join(group_by)}
                      FROM (SELECT COUNT(*) as tmp, {','.join(group_by)}
                            FROM conditions
                            WHERE {condition_str}
                            GROUP BY {','.join(group_by)})
                      WHERE tmp > 1"""
        conditions = self._select(request)
        ids = []
        for condition in conditions:
            request = f"""SELECT id FROM conditions
                          WHERE ({','.join(group_by)}) ==
                            ({','.join([f'"{v}"' if isinstance(v, str) else str(v)
                                        for v in condition])})"""
            ids.append(self._select(request))
        if not ids:
            return {}, ""
        assert len(ids) == 1  # Don't need more at the moment
        ids = ids[0]

        conditions_str = ", ".join([f"{cond}={conditions[0][i]}"
                                    for i, cond in enumerate(group_by)])

        index = []
        for condition in ids:
            tmp = self._select(f"""SELECT {','.join(depending)} FROM conditions
                                   WHERE id = {condition}""")
            try:
                index.append(Connectivity(*tmp[0]))
            except ValueError:
                index.append(tmp[0][0])
            except TypeError:
                index.append(tmp[0])

        if country_dependent:
            countries = self._select("SELECT DISTINCT(country) FROM experiments")
            res = {}
            for country in countries:
                res[country] = {}
                for i, cond in enumerate(ids):
                    res[country][index[i]] = self._select(
                        f"""SELECT id FROM experiments
                            WHERE country=\"{country}\" AND condition = {cond}""")
                    if res[country][index[i]] == []:
                        del res[country][index[i]]
                if res[country] == {}:
                    del res[country]
            return res, conditions_str
        res = {}
        for i, cond in enumerate(ids):
            res[index[i]] = self._select(f"SELECT id FROM experiments WHERE condition = {cond}")
            if res[index[i]] == []:
                del res[index[i]]
        return res, conditions_str
