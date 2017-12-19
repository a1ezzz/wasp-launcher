# -*- coding: utf-8 -*-
# wasp_launcher/core_broker.py
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

from abc import abstractmethod, abstractclassmethod

from wasp_general.verify import verify_type, verify_value
from wasp_general.command.proto import WCommandResultProto
from wasp_general.command.enhanced import WEnhancedCommand
from wasp_general.command.command import WTemplateResultCommand
from wasp_general.command.result import WPlainCommandResult

from wasp_launcher.core import WAppsGlobals, WSyncApp
from wasp_launcher.core_scheduler import WLauncherScheduleTask, WLauncherScheduleRecord


class WBrokerCommandDescription:

	@abstractmethod
	def brief_description(self):
		raise NotImplementedError('This method is abstract')

	def detailed_description(self):
		raise NotImplementedError('This method is abstract')


# noinspection PyAbstractClass
class WBrokerCommand(WEnhancedCommand, WBrokerCommandDescription):

	def detailed_description(self):
		info = 'This is help information for "%s" command (%s). ' % (self.command_token(), self.brief_description())

		arguments_help = self.arguments_help()
		if len(arguments_help) == 0:
			info += 'Command does not have arguments\n'
		else:
			info += 'Command arguments:\n'
			for argument_name, argument_description in arguments_help:
				info += '\t%s - %s\n' % (argument_name, argument_description)
		return info


# noinspection PyAbstractClass
class WTemplateBrokerCommand(WTemplateResultCommand, WBrokerCommandDescription):

	@verify_type('paranoid', command_tokens=str, template_context=(dict, None))
	@verify_type(template_id=str)
	@verify_value(template_id=lambda x: len(x) > 0)
	def __init__(self, template_id, *command_tokens, template_context=None):
		WTemplateResultCommand.__init__(
			self, WAppsGlobals.templates.lookup(template_id), *command_tokens,
			template_context=template_context
		)

	def command_token(self):
		return self.command()[0]

	def detailed_description(self):
		info = 'This is help information for "%s" command (%s). Command does not have arguments\n'
		return info % (self.command_token(), self.brief_description())


class WCommandKit(WSyncApp):

	__dependency__ = [
		'com.binblob.wasp-launcher.apps.broker::init'
	]

	# noinspection PyMethodParameters
	@abstractclassmethod
	def commands(cls):
		"""

		:return: WCommand
		"""
		raise NotImplementedError('This method is abstract')

	@classmethod
	def config_section(cls):
		return 'wasp-launcher::applications::%s' % cls.name()

	def kit_context(self):
		return WAppsGlobals.config[self.config_section()]['kit_context']

	def alias(self):
		section_name = self.config_section()
		if WAppsGlobals.config.has_option(section_name, 'alias') is True:
			return WAppsGlobals.config[section_name]['alias']

	def start(self):
		WAppsGlobals.broker_commands.add_kit(self)

	def stop(self):
		pass


class WResponsiveTask:

	@verify_type('paranoid', task=WLauncherScheduleTask, task_group_id=(str, None))
	@verify_value('paranoid', on_drop=lambda x: x is None or callable(x))
	@verify_value('paranoid', on_wait=lambda x: x is None or callable(x))
	@verify_type(task_source=str, scheduler_instance=(str, None))
	@verify_value(task_source=lambda x: len(x) > 0, scheduler_instance=lambda x: x is None or len(x) > 0)
	def __init__(
		self, task, task_source, scheduler_instance=None, policy=None, task_group_id=None, on_drop=None,
		on_wait=None
	):
		self.__scheduler_instance = scheduler_instance
		self.__task_source = task_source
		self.__record = WLauncherScheduleRecord(
			task, policy=policy, task_group_id=task_group_id, on_drop=on_drop, on_wait=on_wait
		)

	def schedule_record(self):
		return self.__record

	def scheduler_instance(self):
		return self.__scheduler_instance

	def task_source(self):
		return self.__task_source

	def submit_task(self):
		scheduler_name = self.scheduler_instance()
		task_source_name = self.task_source()
		task_source = WAppsGlobals.scheduler.task_source(task_source_name, scheduler_name)

		if task_source is None:
			return WPlainCommandResult.error('Unable to find suitable scheduler. Command rejected')

		schedule_record = self.schedule_record()
		task_uid = schedule_record.task_uid()
		if WAppsGlobals.broker_calls is None:
			WAppsGlobals.log.error('Unable to register task "%s" in calls registry' % task_uid)
		else:
			WAppsGlobals.broker_calls.add_task(task_uid, scheduler_name)
		task_source.add_record(schedule_record)
		return WPlainCommandResult('Task submitted. Task id: %s' % task_uid, broker_last_task=task_uid)

	@classmethod
	@verify_type(task=WLauncherScheduleTask, command_result=WCommandResultProto)
	def submit_result(cls, task, command_result):
		WAppsGlobals.broker_calls.set_result(task.uid(), command_result)


class WResponsiveBrokerCommand(WBrokerCommand):

	__scheduler_instance__ = None
	__task_source_name__ = None

	class ScheduledTask(WLauncherScheduleTask):

		__task_name__ = 'Scheduled task for responsive command'

		def __init__(self, basic_command, *command_tokens, **command_env):
			WLauncherScheduleTask.__init__(self)
			self.__basic_command = basic_command
			self.__command_tokens = command_tokens
			self.__command_env = command_env

		def basic_command(self):
			return self.__basic_command

		def thread_started(self):
			result = self.__basic_command.exec(*self.__command_tokens, **self.__command_env)
			WResponsiveTask.submit_result(self, result)

		def name(self):
			return self.__task_name__

		def brief_description(self):
			return self.__basic_command.brief_description()

	def __init__(self, basic_broker_command, scheduled_task_cls=None):
		WBrokerCommand.__init__(
			self, basic_broker_command.command_token(), *basic_broker_command.argument_descriptors(),
			relationships=basic_broker_command.relationships()
		)
		self.__basic_command = basic_broker_command
		self.__scheduled_task_cls = \
			scheduled_task_cls if scheduled_task_cls is not None else WResponsiveBrokerCommand.ScheduledTask

	def basic_command(self):
		return self.__basic_command

	def exec(self, *command_tokens, **command_env):
		WBrokerCommand.exec(self, *command_tokens, **command_env)  # just for check
		task = self.create_task(*command_tokens, **command_env)
		rt = WResponsiveTask(task, self.__task_source_name__, scheduler_instance=self.__scheduler_instance__)
		return rt.submit_task()

	def _exec(self, command_arguments, **command_env):
		pass

	def create_task(self, *command_tokens, **command_env):
		"""
		:return: WLauncherScheduleTask
		"""
		return self.__scheduled_task_cls(self.basic_command(), *command_tokens, **command_env)

	def brief_description(self):
		return self.basic_command().brief_description()
