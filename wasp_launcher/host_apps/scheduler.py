# -*- coding: utf-8 -*-
# wasp_launcher/host_apps/scheduler.py
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

# TODO: document the code
# TODO: write tests for the code

# noinspection PyUnresolvedReferences
from wasp_launcher.version import __author__, __version__, __credits__, __license__, __copyright__, __email__
# noinspection PyUnresolvedReferences
from wasp_launcher.version import __status__

from wasp_general.task.thread import WThreadJoiningTimeoutError
from wasp_general.task.scheduler.scheduler import WTaskSchedulerService, WSchedulerWatchingDog

from wasp_launcher.apps import WSyncHostApp, WAppsGlobals


class WLauncherWatchingDog(WSchedulerWatchingDog):

	def stop(self):
		try:
			WSchedulerWatchingDog.stop(self)
		except WThreadJoiningTimeoutError:
			task_id = self.task_schedule().task_id()
			WAppsGlobals.log.error('Unable to stop scheduled task gracefully. Task id: %s' % str(task_id))


class WSchedulerHostApp(WSyncHostApp):

	__registry_tag__ = 'com.binblob.wasp-launcher.host-app.scheduler'

	__dependency__ = [
		'com.binblob.wasp-launcher.host-app.guest-apps'
	]

	def start(self):
		if WAppsGlobals.scheduler is None:
			WAppsGlobals.scheduler = WTaskSchedulerService(watching_dog_cls=WLauncherWatchingDog)
			# TODO: make cron source public
			#WAppsGlobals.scheduler_cron_source = WCronTaskSource(WAppsGlobals.scheduler)
			#WAppsGlobals.scheduler.add_task_source(WAppsGlobals.scheduler_cron_source)
			WAppsGlobals.scheduler.start()

	def stop(self):
		if WAppsGlobals.scheduler is not None:
			WAppsGlobals.scheduler.stop()
			WAppsGlobals.scheduler = None
