# -*- coding: utf-8 -*-
# wasp_launcher/apps/broker_commands.py
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

import traceback
import threading
import time

from wasp_general.verify import verify_type, verify_value

from wasp_general.command.command import WCommandResult, WCommandProto, WCommand, WReduceCommand
from wasp_general.command.command import WCommandSelector, WCommandPrioritizedSelector
from wasp_general.command.context import WContextProto, WContext, WCommandContextResult, WCommandContextAdapter
from wasp_general.command.context import WCommandContext, WCommandContextSet
from wasp_general.datetime import local_datetime

from wasp_launcher.core import WAppsGlobals, WCommandKit, WBrokerCommand
from wasp_launcher.loader import WClassLoader


class WBrokerCommandManager:
	"""
	WBrokerCommandManager.__internal_set - static help information
		|
		| - - - - > core_set (BrokerCommandSet(WCommandPrioritizedSelector)) - static help information
		|                 | - - - > ... (WCommandPrioritizedSelector) - dynamic help information
		|                 |          | - - - > (WCommand) - dynamic help information
		|                 |          | - - - > (WCommand) - dynamic help information
		|                 | - - - > ... (WCommandPrioritizedSelector) - dynamic help information
		|
		| - - - - > general_apps_set (BrokerCommandSet (WCommandPrioritizedSelector)) - static help information
		|                 | - - - > ... (WCommandPrioritizedSelector) - dynamic help information
		|                 |          | - - - > (WCommand) - dynamic help information
		|                 |          | - - - > (WCommand) - dynamic help information
		|                 | - - - > ... (WCommandPrioritizedSelector) - dynamic help information
		|
		| - - - - > dot (WCommand)
		| - - - - > double dot (WCommand)
	"""

	__general_usage_help__ = """It is a help system. It can be used in any context. It can be called directly for particular help section like:
	- help <[core|apps] <[module name or alias] <command>>>
	- [core|apps] help
	- [core|apps] [module name or alias] help
	- [core|apps] [module name or alias] help [command]

Or it can be called inside a context by calling 'help', in that case - result will be different for different context

You can change current context by calling a command:
	- [core|apps] <[module name or alias]>

Inside a context you can switch to main context with a single dot command  ('.') or to one-level higher context with \
double dot command ('..').

You can call a specific command in any context by the following pattern:
	- [core|apps] [module or alias] [command] <command_arg1> <command_arg2...>
"""
	__general_usage_tip__ = """For detailed information about command line usage - type 'help help'
"""

	__main_context_help__ = """This is a main or root context. Suitable sub-context are:
	- core
	- apps
"""
	__core_level_context_help__ = """This is a 'core' context. Context for modules and commands that \
interact with "cores". You are able to switch to next context:
"""
	__general_apps_level_context_help__ = """This is a 'apps' context. Context for modules and commands that \
interact with "appss". You are able to switch to next context:
"""

	__specific_app_context_help__ = """This is help for "%s" of "%s" context. Suitable commands are:
"""

	class DoubleDotCommand(WCommand):

		def __init__(self):
			WCommand.__init__(self, '..')

		@verify_type('paranoid', command_tokens=str)
		@verify_type(request_context=(WContextProto, None))
		def _exec(self, *command_tokens, request_context=None, **command_env):
			if request_context is not None:
				return WCommandContextResult(context=request_context.linked_context())
			return WCommandContextResult()

	class DotCommand(WCommand):

		def __init__(self):
			WCommand.__init__(self, '.')

		@verify_type('paranoid', command_tokens=str, request_context=(WContextProto, None))
		def _exec(self, *command_tokens, request_context=None, **command_env):
			return WCommandContextResult()

	class GeneralUsageHelpCommand(WCommandProto):

		def __init__(self):
			WCommandProto.__init__(self)

		@verify_type(command_tokens=str)
		def match(self, *command_tokens, **command_env):
			if command_tokens == ('help', 'help'):
				return True
			return False

		@verify_type('paranoid', command_tokens=str)
		def exec(self, *command_tokens, **command_env):
			if self.match(*command_tokens, **command_env) is False:
				raise RuntimeError('Invalid tokens')
			return WCommandResult(output=WBrokerCommandManager.__general_usage_help__)

	class ContextHelpCommand(WCommandProto):

		@verify_type(command_set=WCommandSelector, help_command=(str, None))
		@verify_value(help_fn=lambda x: callable(x), help_command=lambda x: x is None or len(x) > 0)
		def __init__(self, help_fn, command_set, help_command=None):
			WCommandProto.__init__(self)
			self.__help_fn = help_fn
			self.__command_set = command_set
			self.__help_command = help_command if help_command is not None else 'help'

		def help_info(self):
			return self.__help_fn()

		def command_set(self):
			return self.__command_set

		def help_command(self):
			return self.__help_command

		@verify_type('paranoid', request_context=(WContextProto, None))
		@verify_type(command_tokens=str)
		def match(self, *command_tokens, request_context=None, **command_env):
			if len(command_tokens) > 0:
				if command_tokens[0] == self.help_command():
					if len(command_tokens) == 1:
						return True
					tokens = [command_tokens[1], command_tokens[0]]
					tokens.extend(command_tokens[2:])
					command = self.command_set().select(
						*tokens, request_context=request_context, **command_env
					)
					return command is not None
			return False

		@verify_type('paranoid', command_tokens=str, request_context=(WContextProto, None))
		def exec(self, *command_tokens, request_context=None, **command_env):
			if self.match(*command_tokens, request_context=request_context, **command_env) is False:
				raise RuntimeError('Invalid tokens')
			if len(command_tokens) == 1:
				return WCommandResult(output=self.help_info())
			tokens = [command_tokens[1], command_tokens[0]]
			tokens.extend(command_tokens[2:])
			command = self.command_set().select(*tokens, request_context=request_context, **command_env)
			return command.exec(*tokens, request_context=request_context, **command_env)

	class SpecificCommandHelp(WCommandProto):

		@verify_type(command=WBrokerCommand, help_info=str, help_command=(str, None))
		@verify_value(help_info=lambda x: len(x) > 0, help_command=lambda x: x is None or len(x) > 0)
		def __init__(self, command, help_command=None):
			WCommandProto.__init__(self)
			self.__command = command
			self.__help_command = help_command if help_command is not None else 'help'

		def command(self):
			return self.__command

		def help_command(self):
			return self.__help_command

		@verify_type(command_tokens=str)
		def match(self, *command_tokens, **command_env):
			if command_tokens == (self.help_command(), self.command().command()):
				return True
			return False

		@verify_type('paranoid', command_tokens=str)
		def exec(self, *command_tokens, **command_env):
			if self.match(*command_tokens, **command_env) is False:
				raise RuntimeError('Invalid tokens')
			help_info = self.command().detailed_description()
			help_info += '\n' + WBrokerCommandManager.__general_usage_tip__
			return WCommandResult(output=help_info)

	class UnknownHelpCommand(WCommandProto):

		@verify_type(help_command=(str, None))
		@verify_value(help_command=lambda x: x is None or len(x) > 0)
		def __init__(self, help_command=None):
			WCommandProto.__init__(self)
			self.__help_command = help_command if help_command is not None else 'help'

		def help_command(self):
			return self.__help_command

		@verify_type(command_tokens=str)
		def match(self, *command_tokens, **command_env):
			if len(command_tokens) > 1:
				return command_tokens[0] == self.help_command()
			return False

		@verify_type('paranoid', command_tokens=str)
		def exec(self, *command_tokens, **command_env):
			if self.match(*command_tokens, **command_env) is False:
				raise RuntimeError('Invalid tokens')
			help_info = 'Unknown help section: %s\n' % self.join_tokens(*command_tokens[1:])
			help_info += WBrokerCommandManager.__general_usage_tip__
			return WCommandResult(output=help_info)

	class BrokerContextCommand(WCommandProto):

		@verify_type(main_context=str, app_name=(str, None))
		def __init__(self, main_context, app_name=None):
			self.__main_context = main_context
			self.__app_name = app_name

		@verify_type(command_tokens=str)
		def match(self, *command_tokens, **command_env):
			tokens_count = len(command_tokens)
			if tokens_count == 0:
				return True
			return False

		@verify_type(command_tokens=str)
		def exec(self, *command_tokens, **command_env):
			if len(command_tokens) == 0:
				context = WContext(self.__main_context)
				if self.__app_name is not None:
					context = WContext(self.__app_name, linked_context=context)

				return WCommandContextResult(context=context)

			raise RuntimeError('Invalid tokens')

	class BrokerContextAdapter(WCommandContextAdapter):

		@verify_type(command_tokens=str, request_context=(WContextProto, None))
		def adapt(self, *command_tokens, request_context=None):
			if request_context is None:
				return command_tokens

			result = [request_context.context_name()]
			result.extend(command_tokens)
			return tuple(result)

	class BrokerCommandSet(WCommandPrioritizedSelector):

		@verify_type('paranoid', default_priority=int)
		@verify_type(main_command_set=WCommandPrioritizedSelector, main_context=str)
		@verify_value(main_context=lambda x: len(x) > 0, context_help_info=lambda x: callable(x))
		def __init__(self, main_command_set, main_context, context_help_fn, default_priority=30):
			WCommandPrioritizedSelector.__init__(self, default_priority=default_priority)
			self.__main_command_set = main_command_set
			self.__main_context = main_context

			self.add_prioritized(WBrokerCommandManager.BrokerContextCommand(self.__main_context), 10)
			self.add_prioritized(WBrokerCommandManager.ContextHelpCommand(context_help_fn, self), 50)
			self.add_prioritized(WBrokerCommandManager.UnknownHelpCommand(), 70)

			reduce_command = WReduceCommand(self, self.__main_context)
			main_context_adapter = WBrokerCommandManager.BrokerContextAdapter(WContext(self.__main_context))
			main_context_command = WCommandContext(reduce_command, main_context_adapter)

			self.__main_command_set.add_prioritized(main_context_command, 20)
			self.__main_command_set.add_prioritized(reduce_command, 30)

		@verify_type(context_name=str, commands=WBrokerCommand, force_context_command=bool, alias=(str, None))
		@verify_value(context_name=lambda x: len(x) > 0, app_context_help_fn=lambda x: callable(x))
		@verify_value(alias=lambda x: x is None or len(x) > 0)
		def add_commands(
			self, context_name, app_context_help_fn, *commands, force_context_command=False, alias=None
		):
			if force_context_command is True or len(commands) > 0:
				app_names = (context_name,) if alias is None else (context_name, alias)
				app_commands = WCommandPrioritizedSelector()
				app_commands.add_prioritized(
					WBrokerCommandManager.BrokerContextCommand(self.__main_context, context_name),
					10
				)
				app_commands.add_prioritized(WBrokerCommandManager.UnknownHelpCommand(), 80)

				help_fn = lambda: app_context_help_fn(context_name, commands)
				app_commands.add_prioritized(
					WBrokerCommandManager.ContextHelpCommand(help_fn, app_commands), 50
				)

				for command in commands:
					app_commands.add(command)
					app_commands.add_prioritized(
						WBrokerCommandManager.SpecificCommandHelp(command), 40
					)

				app_context_adapter = WBrokerCommandManager.BrokerContextAdapter(
					WContext(context_name, linked_context=WContext(self.__main_context))
				)
				app_context_command = WCommandContext(
					WReduceCommand(app_commands, *app_names), app_context_adapter
				)

				self.__main_command_set.add_prioritized(app_context_command, 20)
				self.add_prioritized(WReduceCommand(app_commands, *app_names), 30)

	__kit_section_prefix__ = 'wasp-launcher::broker::kits'

	def __init__(self):
		self.__loader = WClassLoader(self.__kit_section_prefix__, WCommandKit, tag_fn=lambda x: x.name())

		self.__internal_set = WCommandContextSet()
		self.__internal_set.commands().add_prioritized(WBrokerCommandManager.DotCommand(), 10)
		self.__internal_set.commands().add_prioritized(WBrokerCommandManager.DoubleDotCommand(), 10)

		self.__internal_set.commands().add_prioritized(WBrokerCommandManager.GeneralUsageHelpCommand(), 15)

		self.__internal_set.commands().add_prioritized(
			WBrokerCommandManager.ContextHelpCommand(
				self.__main_context_help, self.__internal_set.commands()
			), 50
		)

		self.__internal_set.commands().add_prioritized(WBrokerCommandManager.UnknownHelpCommand(), 60)

		main_command_set = self.__internal_set.commands()
		self.__core_apps = []
		self.__total_core_commands = 0
		self.__core_set = WBrokerCommandManager.BrokerCommandSet(
			main_command_set, 'core', self.__core_context_help
		)
		self.__general_apps = []
		self.__total_general_apps_commands = 0
		self.__general_apps_set = WBrokerCommandManager.BrokerCommandSet(
			main_command_set, 'apps', self.__general_app_context_help
		)

	def core_commands(self):
		return self.__total_core_commands

	def general_app_commands(self):
		return self.__total_general_apps_commands

	def __main_context_help(self):
		return self.__main_context_help__ + self.__general_usage_tip__

	def __core_context_help(self):
		help_info = self.__core_level_context_help__
		for app, alias in self.__core_apps:
			if alias is not None:
				help_info += '\t- %s | %s - %s\n' % (alias, app.name(), app.brief_description())
			else:
				help_info += '\t- %s\n - %s' % (app.name(), app.brief_description())
		help_info += '\n'
		help_info += self.__general_usage_tip__
		return help_info

	def __general_app_context_help(self):
		help_info = self.__general_apps_level_context_help__
		for app, alias in self.__general_apps:
			if alias is not None:
				help_info += '\t- %s | %s - %s\n' % (alias, app.name(), app.brief_description())
			else:
				help_info += '\t- %s - %s\n' % (app.name(), app.brief_description())
		help_info += '\n'
		help_info += self.__general_usage_tip__
		return help_info

	def __specific_context_help_templ(self, context_name, app_name, commands):
		help_info = self.__specific_app_context_help__ % (app_name, context_name)
		for command in commands:
			help_info += '\t- %s - %s\n' % (command.command(), command.brief_description())
		help_info += '\n'
		help_info += self.__general_usage_tip__
		return help_info

	def __specific_app_context_help(self, app_name, commands):
		return self.__specific_context_help_templ('apps', app_name, commands)

	def __specific_core_context_help(self, app_name, commands):
		return self.__specific_context_help_templ('core', app_name, commands)

	def load_apps(self):
		self.__loader.load(self.load_callback)

	def load_callback(self, section_name, item_tag, item_cls):
		alias = None
		if WAppsGlobals.config.has_option(section_name, 'alias') is True:
			alias = WAppsGlobals.config[section_name]['alias']

		commands = item_cls.commands()

		if WAppsGlobals.config.getboolean(section_name, 'core') is True:
			self.__core_apps.append((item_cls, alias))

			self.__core_set.add_commands(
				item_tag, self.__specific_core_context_help, *commands, alias=alias,
				force_context_command=True
			)
			self.__total_core_commands += len(commands)
		else:
			self.__general_apps.append((item_cls, alias))
			self.__general_apps_set.add_commands(
				item_tag, self.__specific_app_context_help, *commands, alias=alias
			)
			self.__total_general_apps_commands += len(commands)

	@verify_type('paranoid', command_tokens=str, request_context=(WContextProto, None))
	def exec_broker_command(self, *command_tokens, request_context=None):
		command_obj = self.__internal_set.commands().select(*command_tokens, request_context=request_context)

		if command_obj is None:
			return WCommandResult(output='No suitable command found', error=1)

		try:
			return command_obj.exec(*command_tokens, request_context=request_context)
		except Exception:
			return WCommandResult(
				output='Command execution error. Traceback\n%s' % traceback.format_exc(), error=1
			)


class WCLITableRender:

	__default_delimiter__ = '*'

	@verify_type(table_headers=str)
	def __init__(self, *table_headers):
		self.__headers = table_headers
		self.__rows = []

		self.__cells_length = self.cells_length(*table_headers)

	def cells_length(self, *cells):
		return tuple([len(x) for x in cells])

	def add_row(self, *cells):
		self.__rows.append(cells)
		row_length = self.cells_length(*cells)

		min_cells, max_cells = row_length, self.__cells_length
		if len(cells) > len(max_cells):
			min_cells, max_cells = max_cells, min_cells

		result = [max(min_cells[i], max_cells[i]) for i in range(len(min_cells))]
		result.extend([max_cells[i] for i in range(len(min_cells), len(max_cells))])
		self.__cells_length = tuple(result)

	def render(self, delimiter=None):
		if delimiter is None:
			delimiter = self.__default_delimiter__

		cell_count = len(self.__cells_length)
		if cell_count == 0:
			raise RuntimeError('Empty table')

		separator_length = ((cell_count - 1) * 3) + 4
		for cell_length in self.__cells_length:
			separator_length += cell_length

		separator = (delimiter * separator_length) + '\n'
		left_border = '%s ' % delimiter
		int_border = ' %s ' % delimiter
		right_border = ' %s\n' % delimiter

		def render_row(*cells):
			row_result = ''
			for i in range(cell_count):
				cell_length = self.__cells_length[i]
				if i < len(cells):
					single_cell = cells[i]
					row_result += single_cell
					delta = (cell_length - len(single_cell))
				else:
					delta = cell_length
				row_result += ' ' * delta

				if i < (cell_count - 1):
					row_result += int_border

			return row_result

		result = separator
		result += left_border
		result += render_row(*self.__headers)
		result += right_border
		result += separator

		for row in self.__rows:
			result += left_border
			result += render_row(*row)
			result += right_border

		result += separator

		return result


class WHealthCommandKit(WCommandKit):

	__kit_name__ = 'com.binblob.wasp-launcher.broker.kits.health'

	class Threads(WBrokerCommand):

		def __init__(self):
			WBrokerCommand.__init__(self, 'threads')

		@verify_type(command_arguments=dict)
		def _exec(self, command_arguments):
			threads = threading.enumerate()

			table_render = WCLITableRender('Thread name')
			for thread in threads:
				table_render.add_row(thread.name)

			header = 'Total threads: %i\n' % len(threads)
			return WCommandResult(output=header + table_render.render())

		@classmethod
		def brief_description(cls):
			return 'return application threads list'

	@classmethod
	def name(cls):
		return cls.__kit_name__

	@classmethod
	def brief_description(cls):
		return 'general or launcher-wide commands'

	@classmethod
	def commands(cls):
		return [WHealthCommandKit.Threads()]


class WModelDBCommandKit(WCommandKit):

	__kit_name__ = 'com.binblob.wasp-launcher.broker.kits.model-db'

	@classmethod
	def name(cls):
		return cls.__kit_name__

	@classmethod
	def brief_description(cls):
		return 'database schema commands'

	@classmethod
	def commands(cls):
		return []


class WModelObjCommandKit(WCommandKit):

	__kit_name__ = 'com.binblob.wasp-launcher.broker.kits.model-obj'

	@classmethod
	def name(cls):
		return cls.__kit_name__

	@classmethod
	def brief_description(cls):
		return 'model-specific commands'

	@classmethod
	def commands(cls):
		return []


class WAppsCommandKit(WCommandKit):

	__kit_name__ = 'com.binblob.wasp-launcher.broker.kits.apps'

	@classmethod
	def name(cls):
		return cls.__kit_name__

	@classmethod
	def brief_description(cls):
		return 'general application related commands'

	@classmethod
	def commands(cls):
		return []


class WScheduleCommandKit(WCommandKit):

	__kit_name__ = 'com.binblob.wasp-launcher.broker.kits.scheduler'

	class SchedulerInstances(WBrokerCommand):

		def __init__(self):
			WBrokerCommand.__init__(self, 'instances')

		@verify_type(command_arguments=dict)
		def _exec(self, command_arguments):
			if WAppsGlobals.scheduler is None:
				return WCommandResult(output='Scheduler collection was not loaded', error=1)

			table_render = WCLITableRender('Scheduler instance name')
			table_render.add_row('<default instance>')

			named_instances = WAppsGlobals.scheduler.named_instances()
			for instance_name in named_instances:
				table_render.add_row(instance_name)

			header = 'Total instances count: %i\n' % (len(named_instances) + 1)
			return WCommandResult(output=header + table_render.render())

		@classmethod
		def brief_description(cls):
			return 'show started scheduler instances'

	class TaskSources(WBrokerCommand):

		def __init__(self):
			WBrokerCommand.__init__(self, 'sources')

		@verify_type(command_arguments=dict)
		def _exec(self, command_arguments):
			if WAppsGlobals.scheduler is None:
				return WCommandResult(output='Scheduler was not loaded', error=1)

			count = 0

			table_render = WCLITableRender(
				'Scheduler instance', 'Source name', 'Source description', 'Scheduled tasks',
				'Next scheduled task'
			)

			dt_fn = lambda x: '%s%s' % (local_datetime(dt=x).isoformat(), time.strftime('%Z'))
			for instance, instance_name in WAppsGlobals.scheduler:
				if instance_name is None:
					instance_name = '<default instance>'
				task_sources = instance.task_sources()
				for source in task_sources:
					description = source.description()
					if description is None:
						description = '(not available)'

					next_start = source.next_start()
					next_start = dt_fn(next_start) if next_start is not None else '(not available)'

					table_render.add_row(
						instance_name, source.name(), description, str(source.tasks_planned()),
						next_start
					)

				count += len(task_sources)

			header = 'Total sources count: %i\n' % count
			return WCommandResult(output=(header + table_render.render()))

		@classmethod
		def brief_description(cls):
			return 'show tasks sources information'

	class RunningTasks(WBrokerCommand):

		def __init__(self):
			WBrokerCommand.__init__(self, 'running_tasks')

		@verify_type(command_arguments=dict)
		def _exec(self, command_arguments):
			if WAppsGlobals.scheduler is None:
				return WCommandResult(output='Scheduler was not loaded', error=1)

			count = 0

			table_render = WCLITableRender('Scheduler instance',  'Task started at')

			for instance, instance_name in WAppsGlobals.scheduler:
				if instance_name is None:
					instance_name = '<default instance>'

				tasks = instance.running_tasks()
				count += len(tasks)

				dt_fn = lambda x: '%s%s' % (local_datetime(dt=x).isoformat(), time.strftime('%Z'))

				for task in tasks:
					table_render.add_row(instance_name, dt_fn(task.started_at()))

			header = 'Total tasks that run at the moment: %i\n' % count
			return WCommandResult(output=(header + table_render.render()))

		@classmethod
		def brief_description(cls):
			return 'show tasks that run at the moment'

	@classmethod
	def name(cls):
		return cls.__kit_name__

	@classmethod
	def brief_description(cls):
		return 'scheduler commands'

	@classmethod
	def commands(cls):
		return [
			WScheduleCommandKit.SchedulerInstances(),
			WScheduleCommandKit.TaskSources(),
			WScheduleCommandKit.RunningTasks()
		]
