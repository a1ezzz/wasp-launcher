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

from wasp_general.verify import verify_type, verify_value

from wasp_general.task.thread import WThreadJoiningTimeoutError
from wasp_general.task.scheduler.scheduler import WTaskSchedulerService, WSchedulerWatchingDog
from wasp_general.task.scheduler.task_source import WCronTaskSource

from wasp_launcher.apps import WSyncHostApp, WAppsGlobals, WCronTasks


class WLauncherWatchingDog(WSchedulerWatchingDog):

	def stop(self):
		try:
			WSchedulerWatchingDog.stop(self)
		except WThreadJoiningTimeoutError:
			task_id = self.task_schedule().task_id()
			WAppsGlobals.log.error('Unable to stop scheduled task gracefully. Task id: %s' % str(task_id))


class WLauncherScheduler(WTaskSchedulerService):

	@verify_type(maximum_running_tasks=(int, None), maximum_postponed_tasks=(int, None))
	@verify_value(maximum_running_tasks=lambda x: x is None or x > 0)
	@verify_value(maximum_postponed_tasks=lambda x: x is None or x > 0)
	def __init__(self, maximum_running_tasks=None, maximum_postponed_tasks=None):
		WTaskSchedulerService.__init__(
			self, maximum_running_tasks=maximum_running_tasks,
			maximum_postponed_tasks=maximum_postponed_tasks, watching_dog_cls=WLauncherWatchingDog
		)
		self.__cron_source = WCronTaskSource(self)
		self.add_task_source(self.__cron_source)

	def cron_source(self):
		return self.__cron_source


class WSchedulerInitHostApp(WSyncHostApp):

	__registry_tag__ = 'com.binblob.wasp-launcher.host-app.scheduler::init'

	__dependency__ = [
		'com.binblob.wasp-launcher.host-app.config'
	]

	def start(self):
		WAppsGlobals.log.info('Scheduler is initializing')
		if WAppsGlobals.scheduler is None:
			maximum_running_tasks = \
				WAppsGlobals.config.getint('wasp-launcher::scheduler', 'maximum_running_tasks')
			maximum_postponed_tasks = \
				WAppsGlobals.config['wasp-launcher::scheduler']['maximum_postponed_tasks']

			if maximum_postponed_tasks != '':
				maximum_postponed_tasks = int(maximum_postponed_tasks)
			else:
				maximum_postponed_tasks = None

			WAppsGlobals.scheduler = WLauncherScheduler(
				maximum_running_tasks=maximum_running_tasks,
				maximum_postponed_tasks=maximum_postponed_tasks
			)

	def stop(self):
		WAppsGlobals.log.info('Scheduler is finalizing')
		if WAppsGlobals.scheduler is not None:
			WAppsGlobals.scheduler = None


class WSchedulerHostApp(WSyncHostApp):

	__registry_tag__ = 'com.binblob.wasp-launcher.host-app.scheduler::start'

	__dependency__ = [
		'com.binblob.wasp-launcher.host-app.guest-apps'
	]

	def start(self):
		WAppsGlobals.log.info('Scheduler is starting')
		if WAppsGlobals.scheduler is not None:
			WAppsGlobals.scheduler.start()

	def stop(self):
		WAppsGlobals.log.info('Scheduler is stopping')
		if WAppsGlobals.scheduler is not None:
			WAppsGlobals.scheduler.stop()
