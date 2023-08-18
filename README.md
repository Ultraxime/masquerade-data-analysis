|![gplv3-or-later](https://www.gnu.org/graphics/gplv3-or-later.png)|
|-|

# Masquerade Data Analysis

Masquerade Data Analysis is a Python library and programme for dealing with the result of the expriment with masque provided in [masquerade_experiements](https://github.com/Ultraxime/masquerade_experiements)


## Installation

No installation procedure is currently developped.

You can install the dependency as usual
```bash
pip install -Ur requirements.txt
```


## Usage

Currently the project can only run on python 3.10.
To make it work with python >3.10, replace all occurence of `from typing_extensions import Self` with `from typing import Self`

`main.py` provides several options
```bash
# To run it as default
python main.py

# To run it with a custom loglevel (by default it is warning)
python main.py --log {debug,info,warning,error,critical} --logfile LOGFILE

# To run it with the log logged in a file
python main.py --logfile LOGFILE

# To show the help
python main.py --help
```

### Datas

By default, the name of the folder where the datas are stored is `datas` it can modified by changing the argument `folder` for `Results` in `main.py`.
The same way the database is `tmp.db` but can be change by changing the argument `database` for `Results` in `main.py`.

The shape of the folder where the datas are stored is expected as folow :
```bash
datas
├── de
│   ├── 1
│   │   ├── <upload_speed> <download_speed> <RTT> <Loss> [any].yml
│   │   └── <upload_speed> <download_speed> <RTT> <Loss> [any].yml
│   └── 2
│       ├── <upload_speed> <download_speed> <RTT> <Loss> [any].yml
│       └── <network> <quality> <country> <operator> [any].yml
└── it
    └── 1
        └── <network> <quality> <country> <operator> [any].yml

```
Where the first level has to be two ascii caracters representing the country, the second a integer representing the run number of the experiment.
File have to encode the caracteristique of the experiment with either format.

## Contributing

Pull requests are welcome. For major changes, please open an issue first to discuss what you would like to change.

<!-- Please make sure to update tests as appropriate. -->

### Adding Test

To add a test, you need to:
 - add the corresponding table to the database by adding its description in `config.yml`;
 - create a class inheriting the class `src.types:Result` representing the test's result and a class inheriting the class `src.types:Run` used to represent one run o the test;
 - edit the file `src.loader.py` in order for the YAML loader to be able to parse your new class.


### Adding Metric

To add a new metric, you will need to:
 - add their description in `config.yml`;
 - add the corrsponding test if need be.


### Adding Setup

To add a setup, you will need to:
 - modify the class `src.types:Result` by adding a new field for this scenario and modify all the method that refere to the fields;
 - modify the class `src.types:BrowserTime` in the same way that the previous;
 - modify this line `if "masquerade" not in data[condition] or "native" not in data[condition]:` in `src.results.py` if you want this scenario to be mandatory (`masquerade` and `native` are already mandatory).


### Pre-Commit

The project already contains a pre-commit-config, to install the necessary dependencies, run `pip install -Ur pre-commit-requirements.txt`


## Authors

 - [@Ultraxime](https://github.com/Ultraxime)


## License

This program is free software: you can redistribute it and/or modify it under the terms of the GNU General Public License as published by the Free Software Foundation, either version 3 of the License, or (at your option) any later version.

This program is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License for more details.

You should have received a copy of the GNU General Public License along with this program. If not, see <https://www.gnu.org/licenses/>.
