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
from enum import Enum

from wasp_general.verify import verify_type, verify_value

from wasp_general.command.command import WCommandResult, WCommandProto, WReduceCommand, WCommandSelector
from wasp_general.command.command import WCommandPrioritizedSelector, WCommandSet
from wasp_general.command.context import WContextProto, WContext, WCommandContextAdapter, WCommandContext

from wasp_launcher.core_broker import WCommandKit, WBrokerCommand
from wasp_launcher.apps.broker.internal_commands import WBrokerInternalCommandSet


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

	__general_usage_tip__ = 'For detailed information about command line usage - type "help help"\n'

	__main_context_help_header__ = 'This is a main or root context. Suitable sub-context are:\n'

	__specific_app_context_help__ = 'This is help for "%s" of "%s" context. Suitable commands are:\n'

	class MainSections(Enum):
		core = 'core'
		apps = 'apps'

	__help_info__ = {
		MainSections.core: """This is a 'core' context. Context for commands that interact with important
built-in applications. You are able to switch to next context:
""",
		MainSections.apps: """This is a 'apps' context. Context for commands that interact with user-defined
applications. You are able to switch to next context:
"""
	}

	class ContextHelpCommand(WCommandProto):

		@verify_type(command_set=WCommandSelector, help_command=(str, None))
		@verify_value(help_ingfo=lambda x: callable(x) or (isinstance(x, str) and len(x) > 0))
		@verify_value(help_command=lambda x: x is None or len(x) > 0)
		def __init__(self, help_info, command_set, help_command=None):
			WCommandProto.__init__(self)
			self.__help_fn = help_info if callable(help_info) else lambda: help_info
			self.__command_set = command_set
			self.__help_command = help_command if help_command is not None else 'help'

		def help_info(self):
			return self.__help_fn()

		def command_set(self):
			return self.__command_set

		def help_command(self):
			return self.__help_command

		@verify_type('paranoid', command_context=(WContextProto, None))
		@verify_type(command_tokens=str)
		def match(self, *command_tokens, command_context=None, **command_env):
			if len(command_tokens) > 0:
				if command_tokens[0] == self.help_command():
					if len(command_tokens) == 1:
						return True
					tokens = [command_tokens[1], command_tokens[0]]
					tokens.extend(command_tokens[2:])
					command = self.command_set().select(
						*tokens, command_context=command_context, **command_env
					)
					return command is not None
			return False

		@verify_type('paranoid', command_tokens=str, command_context=(WContextProto, None))
		def exec(self, *command_tokens, command_context=None, **command_env):
			if self.match(*command_tokens, command_context=command_context, **command_env) is False:
				raise RuntimeError('Invalid tokens')
			if len(command_tokens) == 1:
				return WCommandResult(output=self.help_info())
			tokens = [command_tokens[1], command_tokens[0]]
			tokens.extend(command_tokens[2:])
			command = self.command_set().select(*tokens, command_context=command_context, **command_env)
			return command.exec(*tokens, command_context=command_context, **command_env)

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

				return WCommandResult(command_context=context)

			raise RuntimeError('Invalid tokens')

	class BrokerContextAdapter(WCommandContextAdapter):

		@verify_type(command_tokens=str, command_context=(WContextProto, None))
		def adapt(self, *command_tokens, command_context=None):
			if command_context is None:
				return command_tokens

			result = [command_context.context_name()]
			result.extend(command_tokens)
			return tuple(result)

	class BrokerCommandSet(WCommandPrioritizedSelector):

		@verify_type('paranoid', default_priority=int)
		@verify_type(main_command_set=WCommandPrioritizedSelector)
		def __init__(self, main_command_set, section, default_priority=30):
			WCommandPrioritizedSelector.__init__(self, default_priority=default_priority)

			if isinstance(section, WBrokerCommandManager.MainSections) is False:
				raise TypeError('Invalid section type')

			self.__main_command_set = main_command_set
			self.__section_name = section.value
			self.__section_help_header = WBrokerCommandManager.__help_info__[section]
			self.__kits = []
			self.__total_commands = 0

			def context_help_fn():
				help_info = self.__section_help_header
				for kit in self.__kits:
					alias = kit.alias()
					name = ('%s | %s' % (alias, kit.name())) if alias is not None else kit.name()
					help_info += '\t- %s - %s\n' % (name, kit.description())
				help_info += '\n'
				help_info += WBrokerCommandManager.__general_usage_tip__
				return help_info

			self.add_prioritized(WBrokerCommandManager.BrokerContextCommand(self.__section_name), 10)
			self.add_prioritized(WBrokerCommandManager.ContextHelpCommand(context_help_fn, self), 50)
			self.add_prioritized(WBrokerCommandManager.UnknownHelpCommand(), 70)

			reduce_command = WReduceCommand(self, self.__section_name)
			main_context_adapter = WBrokerCommandManager.BrokerContextAdapter(WContext(self.__section_name))
			main_context_command = WCommandContext(reduce_command, main_context_adapter)

			self.__main_command_set.add_prioritized(main_context_command, 20)
			self.__main_command_set.add_prioritized(reduce_command, 30)

		def total_commands(self):
			return self.__total_commands

		@verify_type(command_kit=WCommandKit)
		def add_commands(self, command_kit):
			commands = command_kit.commands()
			if len(commands) == 0:
				return

			self.__kits.append(command_kit)
			self.__total_commands += len(commands)

			kit_name = command_kit.name()
			alias = command_kit.alias()
			kit_names = (kit_name,) if alias is None else (kit_name, alias)

			help_info = WBrokerCommandManager.__specific_app_context_help__
			help_info = help_info % (command_kit.name(), self.__section_name)

			app_commands = WCommandPrioritizedSelector()

			for command in commands:
				help_info += '\t- %s - %s\n' % (command.command(), command.brief_description())
				app_commands.add(command)
				app_commands.add_prioritized(WBrokerCommandManager.SpecificCommandHelp(command), 40)

			help_info += '\n'
			help_info += WBrokerCommandManager.__general_usage_tip__
			app_commands.add_prioritized(
				WBrokerCommandManager.ContextHelpCommand(lambda: help_info, app_commands), 50
			)

			app_commands.add_prioritized(
				WBrokerCommandManager.BrokerContextCommand(self.__section_name, kit_name), 10
			)
			app_commands.add_prioritized(WBrokerCommandManager.UnknownHelpCommand(), 80)

			app_context_adapter = WBrokerCommandManager.BrokerContextAdapter(
				WContext(kit_name, linked_context=WContext(self.__section_name))
			)
			app_context_command = WCommandContext(
				WReduceCommand(app_commands, *kit_names), app_context_adapter
			)

			self.__main_command_set.add_prioritized(app_context_command, 20)
			self.add_prioritized(WReduceCommand(app_commands, *kit_names), 30)

	def __init__(self):
		self.__internal_set = WBrokerInternalCommandSet()
		self.__main_sections = {}

		internal_command_set = self.__internal_set.commands()
		help_info = WBrokerCommandManager.__main_context_help_header__
		for section in WBrokerCommandManager.MainSections:
			self.__main_sections[section] = WBrokerCommandManager.BrokerCommandSet(
				internal_command_set, section
			)
			section_name = section.value
			help_info += ('\t - %s\n' % section_name)
		help_info += WBrokerCommandManager.__general_usage_tip__

		context_help_cmd = WBrokerCommandManager.ContextHelpCommand(lambda: help_info, internal_command_set)
		self.__internal_set.commands().add_prioritized(context_help_cmd, 50)
		self.__internal_set.commands().add_prioritized(WBrokerCommandManager.UnknownHelpCommand(), 60)

	def commands_count(self, section=None):
		if section is not None:
			return self.__main_sections[section].total_commands()
		result = 0
		for section_iter in WBrokerCommandManager.MainSections:
			if section_iter in self.__main_sections:
				result += self.__main_sections[section_iter].total_commands()
		return result

	@verify_type(command_kit=WCommandKit)
	def add_kit(self, command_kit):
		broker_section = command_kit.broker_section()
		section = self.__main_sections[WBrokerCommandManager.MainSections(broker_section)]
		section.add_commands(command_kit)

	# noinspection PyBroadException
	@verify_type('paranoid', command_tokens=str, command_context=(WContextProto, None))
	def exec_broker_command(self, *command_tokens, **command_env):
		command_obj = self.__internal_set.commands().select(*command_tokens, **command_env)

		if command_obj is None:
			return WCommandResult(output='No suitable command found', error=1)

		try:
			return command_obj.exec(*command_tokens, **command_env)
		except Exception:
			return WCommandResult(
				output='Command execution error. Traceback\n%s' % traceback.format_exc(), error=1
			)
