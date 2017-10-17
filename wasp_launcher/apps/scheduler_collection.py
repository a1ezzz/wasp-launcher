# -*- coding: utf-8 -*-
# wasp_launcher/apps/scheduler_collection.py
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

import re

from wasp_general.verify import verify_type, verify_value
from wasp_general.command.command import WCommandProto

from wasp_general.task.thread import WThreadJoiningTimeoutError
from wasp_general.task.scheduler.scheduler import WSchedulerService, WRunningRecordRegistry, WSchedulerWatchdog
from wasp_general.task.scheduler.task_source import WCronTaskSource, WCronLocalTZSchedule, WCronScheduleRecord
from wasp_general.task.scheduler.task_source import WCronUTCSchedule

from wasp_launcher.core import WAppsGlobals, WThreadTaskLoggingHandler
from wasp_launcher.core_scheduler import WLauncherScheduleTask, WLauncherTaskSource, WLauncherScheduleRecord


class WLauncherWatchdog(WThreadTaskLoggingHandler, WSchedulerWatchdog):

	@classmethod
	@verify_type('paranoid', record=WLauncherScheduleRecord)
	def create(cls, record, registry):
			if isinstance(record.task(), WLauncherScheduleTask) is False:
				raise TypeError(
					'Scheduled unsupported task. Task must be WLauncherScheduleTask object'
				)
			return WSchedulerWatchdog.create(record, registry)

	def stop(self):
		try:
			WSchedulerWatchdog.stop(self)
		except WThreadJoiningTimeoutError:
			task_uid = self.record().task_uid()
			WAppsGlobals.log.error('Unable to stop scheduled task gracefully. Task id: %s' % task_uid)


class WLauncherConfigTasks(WLauncherTaskSource, WCronTaskSource):

	class BrokerClient(WLauncherScheduleTask):

		def __init__(self, config_option, broker_command):
			WLauncherScheduleTask.__init__(self)
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

		def name(self):
			return 'Executing task "%s" from configuration' % self.__option

		def brief_description(self):
			return 'Task generated from launcher configuration. Requested command: ' + self.__command

	__task_source_name__ = 'com.binblob.wasp-launcher.app.scheduler.config'

	__task_import_re__ = re.compile(
		'^(local|utc)?\\s*(\\d+|\*)\\s*(\\d+|\*)\\s*(\\d+|\*)\\s*(\\d+|\*)\\s*(\\d+|\*)\\s*(\\w+.*)$'
	)

	def __init__(self, scheduler):
		WLauncherTaskSource.__init__(self)
		WCronTaskSource.__init__(self, scheduler)

	def name(self):
		return self.__task_source_name__

	def description(self):
		return 'Fixed tasks that were specified in configuration during start'

	@verify_type(task=WCronScheduleRecord)
	def add_record(self, schedule_record):
		WCronTaskSource.add_record(self, schedule_record.task())

	def load_tasks(self, config_section):
		tasks_options = WAppsGlobals.config.options(config_section)
		for option_name in tasks_options:
			task_cmd = WAppsGlobals.config[config_section][option_name]
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
			record = WCronScheduleRecord(task_schedule, broker_command)
			self.add_record(record)
			WAppsGlobals.log.info('Scheduled config-task "%s" loaded' % option_name)


class WLauncherScheduler(WThreadTaskLoggingHandler, WSchedulerService):

	@verify_type('paranoid', maximum_running_records=(int, None), maximum_postponed_records=(int, None))
	@verify_type(instance_name=(str, None))
	@verify_value('paranoid', maximum_running_records=lambda x: x is None or x > 0)
	@verify_value('paranoid', maximum_postponed_records=lambda x: x is None or x > 0)
	def __init__(self, maximum_running_records=None, maximum_postponed_records=None, instance_name=None):
		thread_name_suffix = ('-%s' % instance_name) if instance_name is not None else None
		WSchedulerService.__init__(
			self,
			maximum_running_records=maximum_running_records,
			maximum_postponed_records=maximum_postponed_records,
			running_record_registry=WRunningRecordRegistry(
				watchdog_cls=WLauncherWatchdog,
				thread_name_suffix=thread_name_suffix
			),
			thread_name_suffix=thread_name_suffix
		)

	@verify_type(task_source=WLauncherTaskSource)
	def add_task_source(self, task_source):
		WSchedulerService.add_task_source(self, task_source)


class WSchedulerCollection:

	__instance_config_section_re__ = re.compile(
		'wasp-launcher::scheduler::instance(::([a-zA-Z]+[a-zA-Z0-9.\-_]*))?'
	)

	__cron_config_section_prefix__ = 'wasp-launcher::scheduler::cron'

	def __init__(self):
		self.__default_instance = None
		self.__named_instances = {}

	def load_instances(self):
		for section_name in WAppsGlobals.config.sections():
			result = self.__instance_config_section_re__.search(section_name)
			if result is None:
				continue
			instance_name = result.group(2)

			maximum_running_records = WAppsGlobals.config.getint(section_name, 'maximum_running_records')
			maximum_postponed_records = WAppsGlobals.config[section_name]['maximum_postponed_records']

			if maximum_postponed_records != '':
				maximum_postponed_records = int(maximum_postponed_records)
			else:
				maximum_postponed_records = None

			instance = WLauncherScheduler(
				maximum_running_records=maximum_running_records,
				maximum_postponed_records=maximum_postponed_records,
				instance_name=instance_name
			)

			if instance_name is None:
				self.__default_instance = instance
				WAppsGlobals.log.info('New default scheduler instance loaded')
			else:
				self.__named_instances[instance_name] = instance
				WAppsGlobals.log.info('New scheduler instance "%s" loaded' % instance_name)

	def start_instances(self):

		def start(scheduler, name=None):

			if name is None:
				WAppsGlobals.log.info('Starting default scheduler instance')
			else:
				WAppsGlobals.log.info('Starting "%s" scheduler instance' % name)

			scheduler.start()
			cron_section_name = self.__cron_config_section_prefix__
			if name is not None:
				cron_section_name += ('::%s' % name)

			if cron_section_name in WAppsGlobals.config.sections():
				log_msg = 'Loading scheduler tasks from configuration into %s'
				log_msg = log_msg % (('"%s" instance' % name) if name is not None else 'default instance')
				WAppsGlobals.log.info(log_msg)

				cron_source = WLauncherConfigTasks(scheduler)
				cron_source.load_tasks(cron_section_name)
				scheduler.add_task_source(cron_source)

			scheduler.update()

		for instance, name in self:
			start(instance, name)

	def stop_instances(self):
		for instance, name in self:
			instance.stop()

	def instance(self, instance_name=None):
		if instance_name is None:
			return self.__default_instance
		if instance_name in self.__named_instances.keys():
			return self.__named_instances[instance_name]

	def named_instances(self):
		return tuple(self.__named_instances.keys())

	def task_source(self, source_name, instance_name=None):
		instance = self.instance(instance_name=instance_name)
		if instance is None:
			return

		for source in instance.task_sources():
			if source.name() == source_name:
				return source

	def __iter__(self):
		yield (self.__default_instance, None)
		for name, instance in self.__named_instances.items():
			yield (instance, name)
