# -*- coding: utf-8 -*-
# wasp_launcher/apps/kits/scheduler.py
#
# Copyright (C) 2017 the wasp-launcher authors and contributors
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

from wasp_general.verify import verify_type
from wasp_general.cli.formatter import WConsoleTableFormatter, na_formatter, local_datetime_formatter
from wasp_general.command.command import WCommandResult
from wasp_general.task.thread_tracker import WTrackerEvents

from wasp_launcher.core import WAppsGlobals
from wasp_launcher.core_broker import WCommandKit, WBrokerCommand


class WSchedulerCommandKit(WCommandKit):

	__registry_tag__ = 'com.binblob.wasp-launcher.broker.kits.scheduler'

	class SchedulerInstances(WBrokerCommand):

		def __init__(self):
			WBrokerCommand.__init__(self, 'instances')

		@verify_type(command_arguments=dict)
		def _exec(self, command_arguments, **command_env):
			if WAppsGlobals.scheduler is None:
				return WCommandResult(output='Scheduler collection was not loaded', error=1)

			table_formatter = WConsoleTableFormatter(
				'Scheduler instance name',
				'Running tasks',
				'Maximum running tasks',
				'Postponed tasks',
				'Maximum postponed tasks',
			)

			default_instance = WAppsGlobals.scheduler.instance()
			running, postponed = default_instance.records_status()
			table_formatter.add_row(
				'<default instance>',
				str(running),
				str(default_instance.maximum_running_records()),
				str(postponed),
				na_formatter(default_instance.maximum_postponed_records())
			)

			named_instances = WAppsGlobals.scheduler.named_instances()
			for instance_name in named_instances:
				instance = WAppsGlobals.scheduler.instance(instance_name)
				running, postponed = instance.records_status()
				table_formatter.add_row(
					instance_name,
					str(running),
					str(instance.maximum_running_records()),
					str(postponed),
					na_formatter(instance.maximum_postponed_records())
				)

			header = 'Total instances count: %i\n' % (len(named_instances) + 1)
			return WCommandResult(output=header + table_formatter.format())

		@classmethod
		def brief_description(cls):
			return 'show started scheduler instances'

	class TaskSources(WBrokerCommand):

		def __init__(self):
			WBrokerCommand.__init__(self, 'sources')

		@verify_type(command_arguments=dict)
		def _exec(self, command_arguments, **command_env):
			if WAppsGlobals.scheduler is None:
				return WCommandResult(output='Scheduler was not loaded', error=1)

			count = 0

			table_formatter = WConsoleTableFormatter(
				'Scheduler instance', 'Source name', 'Source description', 'Scheduled tasks',
				'Next scheduled task'
			)

			for instance, instance_name in WAppsGlobals.scheduler:
				if instance_name is None:
					instance_name = '<default instance>'
				task_sources = instance.task_sources()
				for source in task_sources:
					description = na_formatter(source.description())
					next_start = na_formatter(source.next_start(), local_datetime_formatter)

					table_formatter.add_row(
						instance_name, source.name(), description, str(source.tasks_planned()),
						next_start
					)

				count += len(task_sources)

			header = 'Total sources count: %i\n' % count
			return WCommandResult(output=(header + table_formatter.format()))

		@classmethod
		def brief_description(cls):
			return 'show tasks sources information'

	class RunningTasks(WBrokerCommand):

		def __init__(self):
			WBrokerCommand.__init__(self, 'running_tasks')

		@verify_type(command_arguments=dict)
		def _exec(self, command_arguments, **command_env):
			if WAppsGlobals.scheduler is None:
				return WCommandResult(output='Scheduler was not loaded', error=1)

			count = 0

			table_formatter = WConsoleTableFormatter(
				'Scheduler instance',  'Task name', 'Task uid', 'Thread', 'Task description'
			)

			for instance, instance_name in WAppsGlobals.scheduler:
				if instance_name is None:
					instance_name = '<default instance>'

				running_records = instance.running_records()
				count += len(running_records)

				for running_record in running_records:
					uid = running_record.task_uid()
					scheduled_task = running_record.task()
					task_name = scheduled_task.name()
					thread_name = na_formatter(scheduled_task.thread_name())
					task_description = scheduled_task.brief_description()

					table_formatter.add_row(
						instance_name, task_name, uid, thread_name, task_description
					)

			header = 'Total tasks that run at the moment: %i\n' % count
			return WCommandResult(output=(header + table_formatter.format()))

		@classmethod
		def brief_description(cls):
			return 'show tasks that run at the moment'

	class History(WBrokerCommand):

		def __init__(self):
			WBrokerCommand.__init__(self, 'history')

		@verify_type(command_arguments=dict)
		def _exec(self, command_arguments, **command_env):
			if WAppsGlobals.scheduler_history is None:
				return WCommandResult(output='Scheduler history is not available', error=1)

			count = 0

			table_formatter = WConsoleTableFormatter(
				'Task name', 'Task uid', 'Status', 'Event time', 'Task description'
			)

			for record in WAppsGlobals.scheduler_history:

				if record.record_type == WTrackerEvents.start:
					status = 'Started'
				elif record.record_type == WTrackerEvents.stop:
					status = 'Stopped'
				elif record.record_type == WTrackerEvents.termination:
					status = 'Terminated'
				elif record.record_type == WTrackerEvents.exception:
					status = 'Exception raised'
				elif record.record_type == WTrackerEvents.wait:
					status = 'Waited'
				elif record.record_type == WTrackerEvents.drop:
					status = 'Dropped'
				else:
					# unknow type
					continue

				table_formatter.add_row(
					record.thread_task.name(),
					record.thread_task.uid(),
					status,
					local_datetime_formatter(record.registered_at),
					record.thread_task.brief_description()
				)
				count += 1

			header = 'Records stored: %i\n' % count
			return WCommandResult(output=(header + table_formatter.format()))

		@classmethod
		def brief_description(cls):
			return 'shows history'

	@classmethod
	def description(cls):
		return 'scheduler commands'

	@classmethod
	def commands(cls):
		return [
			WSchedulerCommandKit.SchedulerInstances(),
			WSchedulerCommandKit.TaskSources(),
			WSchedulerCommandKit.RunningTasks(),
			WSchedulerCommandKit.History()
		]
