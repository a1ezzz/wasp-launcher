# -*- coding: utf-8 -*-
# wasp_launcher/apps/scheduler_app.py
#
# Copyright (C) 2016-2017 the wasp-launcher authors and contributors
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

# TODO: document the code
# TODO: write tests for the code

# noinspection PyUnresolvedReferences
from wasp_launcher.version import __author__, __version__, __credits__, __license__, __copyright__, __email__
# noinspection PyUnresolvedReferences
from wasp_launcher.version import __status__


from wasp_launcher.core import WSyncApp, WAppsGlobals, WSchedulerTaskSourceInstaller
from wasp_launcher.apps.scheduler_collection import WSchedulerCollection


class WSchedulerInitApp(WSyncApp):

	__registry_tag__ = 'com.binblob.wasp-launcher.apps.scheduler::init'

	__dependency__ = [
		'com.binblob.wasp-launcher.apps.config'
	]

	def start(self):
		WAppsGlobals.log.info('Scheduler is initializing')
		if WAppsGlobals.scheduler is None:
			WAppsGlobals.scheduler = WSchedulerCollection()
			WAppsGlobals.scheduler.load_instances()

	def stop(self):
		WAppsGlobals.log.info('Scheduler is finalizing')
		if WAppsGlobals.scheduler is not None:
			WAppsGlobals.scheduler = None


class WSchedulerApp(WSyncApp):

	__registry_tag__ = 'com.binblob.wasp-launcher.apps.scheduler::start'

	__dependency__ = ['com.binblob.wasp-launcher.apps.scheduler::init']

	__dynamic_dependency__ = WSchedulerTaskSourceInstaller

	def start(self):
		WAppsGlobals.log.info('Scheduler is starting')
		if WAppsGlobals.scheduler is not None:
			WAppsGlobals.scheduler.start_instances()

	def stop(self):
		WAppsGlobals.log.info('Scheduler is stopping')
		if WAppsGlobals.scheduler is not None:
			WAppsGlobals.scheduler.stop_instances()
