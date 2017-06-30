#!/usr/bin/python3
# -*- coding: utf-8 -*-
# wasp-launcher.py
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

import signal

from wasp_launcher.apps import WHostAppRegistry, WAppsGlobals
# noinspection PyUnresolvedReferences
import wasp_launcher.host_apps

if __name__ == '__main__':
	print('Launcher is starting')

	config_task = 'com.binblob.wasp-launcher.host-app.config'
	WHostAppRegistry.start_task(config_task)

	host_apps = WAppsGlobals.config.split_option('wasp-launcher::applications', 'host_applications')
	for app in host_apps:
		WHostAppRegistry.start_task(app)

	def shutdown_signal(signum, frame):
		WHostAppRegistry.all_stop()

	signal.signal(signal.SIGTERM, shutdown_signal)
	signal.signal(signal.SIGINT, shutdown_signal)
	signal.pause()
