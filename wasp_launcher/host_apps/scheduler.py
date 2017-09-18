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

from abc import abstractmethod
import re

from wasp_general.verify import verify_type, verify_value
from wasp_general.command.command import WCommandProto

from wasp_general.task.thread import WThreadJoiningTimeoutError
from wasp_general.task.scheduler.proto import WTaskSourceProto, WScheduledTask
from wasp_general.task.scheduler.scheduler import WTaskSchedulerService, WRunningTaskRegistry, WSchedulerWatchdog
from wasp_general.task.scheduler.task_source import WCronTaskSource, WCronLocalTZSchedule, WCronTaskSchedule
from wasp_general.task.scheduler.task_source import WCronUTCSchedule

from wasp_launcher.apps import WSyncHostApp, WAppsGlobals, WThreadTaskLoggingHandler


class WLauncherTaskSource(WTaskSourceProto):

	@abstractmethod
	def name(self):
		raise NotImplementedError('This method is abstract')

	def description(self):
		return None

	@abstractmethod
	def tasks_planned(self):
		raise NotImplementedError('This method is abstract')


class WLauncherConfigTasks(WLauncherTaskSource, WCronTaskSource):

	class BrokerClient(WThreadTaskLoggingHandler, WScheduledTask):

		__thread_name_suffix__ = 'Config-Task-%s'

		def __init__(self, config_option, broker_command):
			WScheduledTask.__init__(self, self.__thread_name_suffix__ % config_option)
			self.__option = config_option
			self.__command = broker_command

		def thread_started(self):
			tokens = WCommandProto.split_command(self.__command)
			result = WAppsGlobals.broker_commands.exec_broker_command(*tokens)
			if result.error is not None:
				WAppsGlobals.log.error(
					'Error in processing scheduled config-task "%s": %s' % (
						self.__option, result.output
					)
				)
			else:
				WAppsGlobals.log.info('Scheduled config-task "%s" completed successfully' % self.__option)

		def thread_stopped(self):
			pass

	__task_source_name__ = 'com.binblob.wasp-launcher.host-app.scheduler.config'

	__task_import_re__ = re.compile(
		'^(local|utc)?\\s*(\\d+|\*)\\s*(\\d+|\*)\\s*(\\d+|\*)\\s*(\\d+|\*)\\s*(\\d+|\*)\\s*(\\w+.*)$'
	)

	__config_section__ = 'wasp-launcher::scheduler::cron'

	def __init__(self, scheduler):
		WLauncherTaskSource.__init__(self)
		WCronTaskSource.__init__(self, scheduler)

	def name(self):
		return self.__task_source_name__

	def description(self):
		return 'Fixed tasks that were specified in configuration during start'

	def tasks_planned(self):
		return WCronTaskSource.tasks_planned(self)

	def load_tasks(self):
		tasks_options = WAppsGlobals.config.options(self.__config_section__)
		for option_name in tasks_options:
			task_cmd = WAppsGlobals.config[self.__config_section__][option_name]
			task_re = self.__task_import_re__.search(task_cmd.lower())
			if task_re is None:
				WAppsGlobals.log.error(
					'Unable to parse configuration task (option: %s). '
					'Task configuration malformed. Check documentation' % option_name
				)
				continue
			task_tokens = task_re.groups()
			schedule_timezone = task_tokens[0]

			if schedule_timezone is None or schedule_timezone == 'local':
				schedule_cls = WCronLocalTZSchedule
			elif schedule_timezone == 'utc':
				schedule_cls = WCronUTCSchedule
			else:
				raise RuntimeError('Internal error. Scheduler is corrupted')

			task_schedule = schedule_cls.from_string_tokens(*task_tokens[1:6])
			broker_command = WLauncherConfigTasks.BrokerClient(option_name, task_tokens[6])
			task = WCronTaskSchedule(task_schedule, broker_command)
			self.add_task(task)
			WAppsGlobals.log.info('Scheduled config-task "%s" loaded' % option_name)


class WLauncherWatchdog(WThreadTaskLoggingHandler, WSchedulerWatchdog):

	def stop(self):
		try:
			WSchedulerWatchdog.stop(self)
		except WThreadJoiningTimeoutError:
			task_id = self.task_schedule().task_id()
			WAppsGlobals.log.error('Unable to stop scheduled task gracefully. Task id: %s' % str(task_id))


class WLauncherScheduler(WThreadTaskLoggingHandler, WTaskSchedulerService):

	@verify_type('paranoid', maximum_running_tasks=(int, None), maximum_postponed_tasks=(int, None))
	@verify_value('paranoid', maximum_running_tasks=lambda x: x is None or x > 0)
	@verify_value('paranoid', maximum_postponed_tasks=lambda x: x is None or x > 0)
	def __init__(self, maximum_running_tasks=None, maximum_postponed_tasks=None):
		WTaskSchedulerService.__init__(
			self, maximum_running_tasks=maximum_running_tasks,
			maximum_postponed_tasks=maximum_postponed_tasks, running_tasks_registry=WRunningTaskRegistry(
				watchdog_cls=WLauncherWatchdog
			)
		)
		self.__cron_source = WLauncherConfigTasks(self)
		self.add_task_source(self.__cron_source)

	def cron_source(self):
		return self.__cron_source

	@verify_type(task_source=WLauncherTaskSource)
	def add_task_source(self, task_source):
		WTaskSchedulerService.add_task_source(self, task_source)


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
			WAppsGlobals.scheduler.cron_source().load_tasks()
			WAppsGlobals.scheduler.update()

	def stop(self):
		WAppsGlobals.log.info('Scheduler is stopping')
		if WAppsGlobals.scheduler is not None:
			WAppsGlobals.scheduler.stop()
