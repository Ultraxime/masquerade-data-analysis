"""
Module for the results class
"""

from sqlite3 import Connection, Cursor, connect
from os import scandir, mkdir
from posix import DirEntry
from typing import Dict, Union, List, Tuple, Optional
import yaml
from pandas import DataFrame
import fastplot

from .types import BrowserTime, SpeedTest, BulkTest, Connectivity
from .loader import Loader


class Results:
    """
    This class describes the results of several experiments.
    """
    _connection: Connection
    _cursor: Cursor

    def __init__(self, folder: str = "datas", database: str = "", name: str = "tmp"):
        if database != "":
            self._connection = connect(database)
            self._cursor = self._connection.cursor()
            return

        self._connection = connect(f"{name}.db")
        self._cursor = self._connection.cursor()

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

        self._cursor.execute("""CREATE TABLE experiments(
                                    id INTEGER PRIMARY KEY NOT NULL,
                                    country char(2) NOT NULL,
                                    run INTEGER NOT NULL,
                                    condition INTEGER NOT NULL,
                                    FOREIGN KEY(condition) REFERENCES conditions(id)
                                )""")

        self._cursor.execute("""CREATE TABLE browsertime(
                                    experimentid INTEGER,
                                    proxy TEXT NOT NULL,
                                    website TEXT NOT NULL,
                                    pageLoadTime INTEGER,
                                    speedIndex INTEGER,
                                    FOREIGN KEY(experimentid) REFERENCES experiments(id)
                                )""")

        self._cursor.execute("""CREATE TABLE speedtest(
                                    experimentid INTEGER,
                                    proxy TEXT NOT NULL,
                                    downloadSpeed REAL NOT NULL,
                                    uploadSpeed REAL NOT NULL,
                                    ping INTEGER NOT NULL,
                                    FOREIGN KEY(experimentid) REFERENCES experiments(id)
                                )""")

        self._cursor.execute("""CREATE TABLE bulktest(
                                    experimentid INTEGER,
                                    proxy TEXT NOT NULL,
                                    downloadSpeed REAL NOT NULL,
                                    FOREIGN KEY(experimentid) REFERENCES experiments(id)
                                )""")

        # pylint: disable=R1702
        for country in scandir(folder):
            if country.is_dir():
                for run in scandir(country.path):
                    if run.is_dir():
                        for experiment in scandir(run.path):
                            if ".yml" in experiment.name:
                                self._add_experiment(experiment, country.name, int(run.name))

    def _select(self, request: str) -> List:
        res = []
        for line in self._cursor.execute(request).fetchall():
            if line is not None:
                res.append(line)
        return res

    def _select_unique(self, request: str) -> List:
        res = []
        for line in self._select(request):
            if line[0] is not None:
                res.append(line[0])
        return res

    def _add_experiment(self, experiment: DirEntry, country: str, run: int):
        data = experiment.name.split(" ")
        try:
            upload = int(data[0])//1000
            download = int(data[1])//1000
            rtt = int(data[2])
            loss = int(data[3])
            condition = self._select_unique(f"""SELECT id FROM conditions
                                                WHERE upload={upload}
                                                    AND download={download}
                                                    AND rtt={rtt}
                                                    AND loss={loss}""")
            if not condition:
                condition = self._select_unique(f"""INSERT INTO conditions (upload, download,
                                                                            rtt, loss)
                                                    VALUES ({upload}, {download}, {rtt}, {loss})
                                                    RETURNING id""")
        except ValueError:
            technology = data[0]
            quality = data[1]
            operator = data[2]
            country = data[3]
            condition = self._select_unique(f"""SELECT id FROM conditions
                                                WHERE technology=\"{technology}\" 
                                                    AND quality=\"{quality}\"
                                                    AND operator=\"{operator}\"
                                                    AND country=\"{country}\"""")
            if not condition:
                condition = self._select_unique(f"""INSERT INTO conditions (technology, quality,
                                                                            operator, country)
                                                    VALUES (\"{technology}\",\"{quality}\",
                                                            \"{operator}\", \"{country}\")
                                                    RETURNING id""")
        assert len(condition) == 1
        condition = condition[0]
        assert isinstance(condition, int)

        experiment_id = self._select_unique(f"""INSERT INTO experiments (country, run, condition)
                                                 VALUES (\"{country}\", {run}, {condition})
                                                 RETURNING id""")
        assert len(experiment_id) == 1
        experiment_id = experiment_id[0]
        assert isinstance(experiment_id, int)

        with open(experiment.path, 'r', encoding='utf-8') as file:
            data = yaml.load(file.read(), Loader=Loader)

        self._insert_browsertime(data["browsertime"], experiment_id)
        self._insert_speedtest(data["speedtest"], experiment_id)
        self._insert_bulktest(data["bulkTest"], experiment_id)

        self._connection.commit()

    def _insert_browsertime(self, browsertime: BrowserTime, experiment_id: int):
        for field in ("native", "masquerade", "squid"):
            for website, result in browsertime.get_field(field).items():
                page_load_time = []
                for test in result.get_page_load_time():
                    if test != 0:
                        page_load_time.append(test)
                speed_index = []
                for test in result.get_speed_index():
                    if test != 0:
                        speed_index.append(test)
                mini = min(len(page_load_time), len(speed_index))
                for i in range(mini):
                    self._cursor.execute(f"""INSERT INTO browsertime
                                             VALUES ({experiment_id}, \"{field}\", \"{website}\",
                                                     {page_load_time[i]}, {speed_index[i]})""")
                for i in range(mini, len(page_load_time)):
                    self._cursor.execute(f"""INSERT INTO browsertime (experimentid, proxy,
                                                                      website, pageLoadTime)
                                             VALUES ({experiment_id}, \"{field}\",
                                                     \"{website}\", {page_load_time[i]})""")
                for i in range(mini, len(speed_index)):
                    self._cursor.execute(f"""INSERT INTO browsertime (experimentid, proxy,
                                                                      website, speedIndex)
                                             VALUES ({experiment_id}, \"{field}\",
                                                     \"{website}\", {speed_index[i]})""")


    def _insert_speedtest(self, speedtest: SpeedTest, experiment_id:  int):
        for field in ("native", "masquerade", "squid"):
            for test in speedtest.get_field(field):
                if (float(test["download_mbps"]) != 0
                    and float(test["download_mbps"]) != 0
                    and int(test["ping_ms"]) != 0):
                    self._cursor.execute(f"""INSERT INTO speedtest
                                             VALUES ({experiment_id},
                                                     \"{field}\",
                                                     {float(test["download_mbps"])},
                                                     {float(test["download_mbps"])},
                                                     {int(test["ping_ms"])})""")

    def _insert_bulktest(self, bulktest: BulkTest, experiment_id: int):
        for field in ("native", "masquerade", "squid"):
            for test in bulktest.get_field(field):
                if int(test) != 0:
                    self._cursor.execute(f"""INSERT INTO bulktest
                                             VALUES ({experiment_id},
                                                     \"{field}\",
                                                     {int(test) / 1000000})""")

    def plot(self):
        """
        Plot all the metrics for all the scenarii
        """
        for depending in ['rtt', 'loss', ['upload', 'download'], ['technology', 'quality']]:
            for country_dependent in [True, False]:
                for metric in ['plt', 'si']:
                    for website_dependent in [True, False]:
                        self.plot_metric(metric, depending, country_dependent, website_dependent)
                for metric in ['ping', 'download', 'upload', 'bulkdownload']:
                    self.plot_metric(metric, depending, country_dependent)

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
        experiments, conditions = self.get_experiment(depending, country_dependent)
        if country_dependent:
            for country, ids in experiments.items():
                assert isinstance(ids, dict)
                data = self.convert(self.get_data(ids, metric, website_dependent),
                                    depending, website_dependent)
                if data is not None:
                    assert isinstance(country, str)
                    self._aux_plot(data, metric, depending, conditions, country, website_dependent)
        else:
            # pylint: disable=C0301
            data = self.convert(
                self.get_data(experiments, metric, website_dependent), # pyright: ignore[reportGeneralTypeIssues]
                depending, website_dependent)
            if data is not None:
                self._aux_plot(data, metric, depending, conditions,
                               website_dependent=website_dependent)

    def convert(self, datas: Union[Dict[str,Dict[int,List]], Dict[int,List]],
                depending: Union[List[str],str], website_dependent: bool = False
               ) -> Optional[Union[Dict[str,DataFrame],DataFrame]]:
        """
        Convert the datas to the corresponding dataframe

        :param      datas:              The datas
        :type       datas:              dict str * (dict int * (list)) | (dict int * (list))
        :param      depending:          The depending
        :type       depending:          str list | str
        :param      website_dependent:  The website dependent
        :type       website_dependent:  bool

        :returns:   the datas
        :rtype:     DataFrame | dict str * DataFrame | Nonetype

        :raises     AssertionError:     if the db is not well built
        """
        if datas == {}:
            return None
        if website_dependent:
            res = {}
            for website, data in datas.items():
                assert isinstance(data, dict)
                res[website] = self.convert(data, depending)
                if res[website] is None:
                    del res[website]
            if not res:
                return None
            return res
        if isinstance(depending, str):
            depending = [depending]
        depending = [x.lower() for x in depending]

        depending_str = ""
        for column in depending:
            depending_str += column + ", "
        depending_str = depending_str[:-2]

        index=[]
        content = []
        for condition, data in datas.items():
            cond = self._select_unique(f"""SELECT {depending_str} FROM conditions
                                           WHERE id = {condition}""")[0]
            try:
                index.append(Connectivity(cond))
            except ValueError:
                index.append(cond)
            content.append(data)
        return DataFrame(content, index=index).sort_index()

    def _aux_plot(self, datas: Union[Dict[str,DataFrame], DataFrame],
                  metric: str, depending: Union[List[str],str],
                  conditions: str, aux: str = "", website_dependent: bool = False):

        if website_dependent:
            for website, data in datas.items():
                assert isinstance(data, DataFrame)
                self._aux_plot(data, metric, depending, conditions, f"{aux} {website}")
            return
        if isinstance(depending, str):
            depending = [depending]
        depending = [x.lower() for x in depending]

        match metric.lower():
            case 'si' | 'plt':
                ylabel = metric.upper() + " (ms)"
            case 'ping':
                ylabel = metric.capitalize() + " (ms)"
            case _:
                ylabel = metric.capitalize() + " (Mbps)"

        match depending:
            case ['rtt']:
                xlabel = "RTT (ms)"
            case ['loss']:
                xlabel = "Loss (%)"
            case ['upload', 'download']:
                xlabel = "Bandwidth (Mbps)"
            case ['technology', 'quality']:
                xlabel = "Network"
            case _:
                raise ValueError(f"Unexpected depending: {depending}")

        if aux:
            aux = f" ({aux})"
        name = f"{metric}/{ylabel} depending on {xlabel} with {conditions}{aux}.png"
        print(name)

        try:
            try:
                mkdir(metric)
            except FileExistsError:
                pass
            fastplot.plot(data=datas, path=name, mode="boxplot_multi",
                          xlabel=xlabel, ylabel=ylabel,
                          legend=True, legend_ncol=3, figsize=(8, 4))
        except ValueError as err:
            print(f"Issue while creating {name}, more than probably, absence of datas")
            print(err)

    def get_data(self, experiments: Dict[int,List[int]],
                 metric: str, website_dependent: bool = False
                ) -> Union[Dict[str,Dict[int,List]], Dict[int,List]]:
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
        match metric:
            case 'plt' | 'si':
                table = "browsertime"
            case 'ping' | 'download' | 'upload':
                table = "speedtest"
            case 'bulkdownload':
                table = "bulktest"
            case _:
                raise ValueError(f"Unknown metric: {metric}")

        match metric:
            case 'plt':
                column = 'pageLoadTime'
            case 'si':
                column = 'speedIndex'
            case 'bulkdownload':
                column = 'downloadSpeed'
            case 'download' | 'upload':
                column = metric + 'Speed'
            case _:
                column = metric

        proxies = self._select_unique(f"SELECT DISTINCT(proxy) FROM {table}")

        if table != "browsertime":
            data = {}
            for condition, experiment_ids in experiments.items():
                if len(experiment_ids) == 1:
                    request = f"""SELECT {column} FROM {table}
                                  WHERE proxy=\"%s\" AND experimentid = {experiment_ids[0]}"""
                else:
                    request = f"""SELECT {column} FROM {table}
                                  WHERE proxy=\"%s\" AND experimentid IN {tuple(experiment_ids)}"""
                data[condition] = {}
                for proxy in proxies:
                    data[condition][proxy] = self._select_unique(request % proxy)
                    if data[condition][proxy] == []:
                        del data[condition][proxy]
                if data[condition] == {}:
                    del data[condition]
            return data
        websites = self._select_unique("SELECT DISTINCT(website) FROM browsertime")
        data = {}
        for website in websites:
            data[website] = {}
            mini = None
            for condition, experiment_ids in experiments.items():
                if len(experiment_ids) == 1:
                    request = f"""SELECT {column} FROM {table}
                                  WHERE proxy=\"%s\" AND website=\"%s\"
                                        AND {column} IS NOT NULL
                                        AND experimentid = {experiment_ids[0]}"""
                else:
                    request = f"""SELECT {column} FROM {table}
                                  WHERE proxy=\"%s\" AND website=\"%s\"
                                        AND {column} IS NOT NULL
                                        AND experimentid IN {tuple(experiment_ids)}"""
                data[website][condition] = {}
                for proxy in proxies:
                    tmp = self._select_unique(request % (proxy, website))
                    data[website][condition][proxy] = tmp
                    if mini:
                        mini = min(mini, len(tmp))
                    else:
                        mini = len(tmp)
            # Strengthening the datas,
            # to be sure that a website is counted the same number of time for every situation
            if mini == 0:
                # print(f"Discarded website: {website}")
                # print(data[website])
                del data[website]
            else:
                for condition in experiments:
                    for proxy in proxies:
                        data[website][condition][proxy] = data[website][condition][proxy][:mini]

        if website_dependent:
            return data
        ret = {}
        for condition in experiments:
            ret[condition] = {}
            for proxy in proxies:
                tmp = []
                for website, datas in data.items():
                    tmp.extend(datas[condition][proxy])
                ret[condition][proxy] = tmp
        return ret

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
        depending_str = ""
        for column in depending:
            depending_str += column + ", "
            group_by.remove(column)
        depending_str = depending_str[:-2]

        group_by_str = ""
        for column in group_by:
            group_by_str += column + ", "
        group_by_str = group_by_str[:-2]

        request = f"""SELECT {group_by_str}
                      FROM (SELECT COUNT(*) as tmp, {group_by_str}
                            FROM conditions
                            WHERE {condition_str}
                            GROUP BY {group_by_str})
                      WHERE tmp > 1"""
        conditions = self._select(request)
        condition_ids = []
        for condition in conditions:
            request = f"""SELECT id FROM conditions
                          WHERE ({group_by_str}) == {condition}"""
            condition_ids.append(self._select_unique(request))
        if not condition_ids:
            return {}, ""
        assert len(condition_ids) == 1  # Don't need more at the moment
        condition = condition_ids[0]

        conditions_str = ""
        for i, cond in enumerate(group_by):
            conditions_str += f"{cond}={conditions[0][i]}, "
        conditions_str = conditions_str[:-2]

        if country_dependent:
            countries = self._select_unique("SELECT DISTINCT(country) FROM experiments")
            res = {}
            for country in countries:
                res[country] = {}
                for cond in condition:
                    res[country][cond] = self._select_unique(
                        f"""SELECT id FROM experiments 
                            WHERE country=\"{country}\" AND condition = {cond}""")
                    if res[country][cond] == []:
                        del res[country][cond]
                if res[country] == {}:
                    del res[country]
            return res, conditions_str
        res = {}
        for cond in condition:
            res[cond] = self._select_unique(f"SELECT id FROM experiments WHERE condition = {cond}")
            if res[cond] == {}:
                del res[cond]
        return res, conditions_str
