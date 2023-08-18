# -*- coding: utf-8 -*-
# @Author: Ultraxime
# @Date:   2023-08-11 16:58:40
# @Last Modified by:   Ultraxime
# @Last Modified time: 2023-08-18 14:44:59
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
Module containing the config file
"""
from typing import Final

import yaml


with open("config.yml", "r", encoding="utf-8") as file:
    CONFIG: Final = yaml.safe_load(file)
