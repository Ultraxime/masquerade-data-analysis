# -*- coding: utf-8 -*-
# @Author: Ultraxime
# @Last Modified by:   Ultraxime
# @Last Modified time: 2023-08-18 18:09:07
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
Main script
"""
import argparse
import logging

from rich.logging import RichHandler

from src import Results

parser = argparse.ArgumentParser(
                    prog='Results compilation',
                    description='Compile the results',
                    epilog='')

parser.add_argument('--log', default=["warning"], nargs=1, required=False, type=str,
                    choices=['debug', 'info', 'warning', 'error', 'critical'])
parser.add_argument('--logfile', default=None, nargs=1, required=False, type=int)

args = parser.parse_args()

numeric_level = getattr(logging, args.log[0].upper(), None)
if not isinstance(numeric_level, int):
    raise ValueError(f'Invalid log level: {args.log}')

options = {'format': '%(message)s',
           'level': numeric_level,
           'handlers': [RichHandler()]}

if args.logfile:
    options['logfile'] = args.logfile[0]

logging.basicConfig(**options)

results = Results()

# results.plot()
# results.plot(country_dependent=True)
# results.plot(full=True)


with open("full_analyse.tex", "w", encoding='utf-8') as file:
    for key, value in results.print_analyse().items():
        file.write(key)
        file.write(value)

with open("country_dep_analyse.tex", "w", encoding='utf-8') as file:
    for key, value in results.print_analyse(country_dependent=True).items():
        file.write(key)
        file.write(value)
