#!/usr/bin/python3
# -*- coding: utf-8 -*-
# wasp_launcher.py
#
# Copyright (C) 2016 the wasp-launcher authors and contributors
# <see AUTHORS file>
#
# This file is part of wasp-launcher.
#
# Wasp-launcher is free software: you can redistribute it and/or modify
# it under the terms of the GNU Lesser General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Wasp-launcher is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Lesser General Public License for more details.
#
# You should have received a copy of the GNU Lesser General Public License
# along with wasp-launcher.  If not, see <http://www.gnu.org/licenses/>.

# noinspection PyUnresolvedReferences
from wasp_launcher.version import __author__, __version__, __credits__, __license__, __copyright__, __email__
# noinspection PyUnresolvedReferences
from wasp_launcher.version import __status__

from wasp_launcher.launcher_registry import WLauncherRegistry

# noinspection PyUnresolvedReferences
from wasp_launcher.log import WLauncherLogSetup
# noinspection PyUnresolvedReferences
from wasp_launcher.config import WLauncherConfig


if __name__ == '__main__':
	print('Launcher is starting')
	WLauncherRegistry.start_task('::wasp_launcher::config::read_config')
