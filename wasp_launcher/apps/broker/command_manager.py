# -*- coding: utf-8 -*-
# wasp_launcher/apps/broker/command_manager.py
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

from wasp_general.command.command import WCommandProto, WReduceCommand, WCommandSelector, WCommand
from wasp_general.command.command import WCommandPrioritizedSelector, WCommandAlias
from wasp_general.command.context import WContextProto, WContext, WCommandContextAdapter, WCommandContext
from wasp_general.command.result import WPlainCommandResult, WExceptionResult
from wasp_general.command.template_command import WCommandResultTemplate

from wasp_launcher.core import WAppsGlobals
from wasp_launcher.core_broker import WCommandKit, WTemplateBrokerCommand
from wasp_launcher.apps.broker.internal_commands import WBrokerInternalCommandSet


class WBrokerCommandManager:
	"""
	WBrokerCommandManager.__internal_set (WBrokerInternalCommandSet) - static help information
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
	"""

	__help_command__ = 'help'

	__general_usage_tip__ = 'For detailed information about command line usage - type "help help"\n'

	class MainKitContext(Enum):
		core = 'core'
		apps = 'apps'

	class HelpCommandAlias(WCommandAlias):

		@verify_type(command_set=WCommandSelector)
		def __init__(self, command_set):
			WCommandAlias.__init__(self, command_set)

		def mutate_command_tokens(self, *command_tokens):
			if len(command_tokens) > 1:
				if command_tokens[0] == WBrokerCommandManager.__help_command__:
					tokens = [command_tokens[1], command_tokens[0]]
					tokens.extend(command_tokens[2:])
					return tokens


	class BrokerHelpCommand(WTemplateBrokerCommand):

		@verify_type('paranoid', template_id=str, template_context=(dict, None))
		@verify_value('paranoid', template_id=lambda x: len(x) > 0)
		def __init__(self, template_id, template_context=None):
			WTemplateBrokerCommand.__init__(
				self, template_id, WBrokerCommandManager.__help_command__,
				template_context=template_context
			)

		def brief_description(self):
			return ''

	class UnknownHelpCommand(WCommand):

		def __init__(self):
			WCommand.__init__(self, WBrokerCommandManager.__help_command__)

		@verify_type(command_tokens=str)
		def match(self, *command_tokens, **command_env):
			if len(command_tokens) > 1:
				return WCommand.match(self, *command_tokens, **command_env)

		@verify_type('paranoid', command_tokens=str)
		def _exec(self, *command_tokens, **command_env):
			result = WCommandResultTemplate(self.command_template())
			result.update_context(invalid_section=self.join_tokens(*command_tokens[1:]))
			return result

		@classmethod
		def command_template(cls):
			return WAppsGlobals.templates.lookup(
				'mako::com.binblob.wasp-launcher.broker::help::unknown_help.mako'
			)

	class BrokerContextCommand(WCommandProto):

		@verify_type(main_context=str, app_name=(str, None))
		def __init__(self, main_context, app_name=None):
			self.__main_context = main_context
			self.__app_name = app_name

		@verify_type(command_tokens=str)
		def match(self, *command_tokens, **command_env):
			if len(command_tokens) == 0:
				return True
			return False

		@verify_type(command_tokens=str)
		def exec(self, *command_tokens, **command_env):
			if len(command_tokens) == 0:
				context = WContext(self.__main_context)
				if self.__app_name is not None:
					context = WContext(self.__app_name, linked_context=context)

				return WPlainCommandResult('', command_context=context)

			raise RuntimeError('Invalid tokens')

	class BrokerContextAdapter(WCommandContextAdapter):

		@verify_type(command_tokens=str, command_context=(WContextProto, None))
		def adapt(self, *command_tokens, command_context=None, **command_env):
			if command_context is None:
				return command_tokens

			result = [command_context.context_name()]
			result.extend(command_tokens)
			return tuple(result)

	class BrokerCommandSet(WCommandPrioritizedSelector):

		@verify_type('paranoid', default_priority=int)
		@verify_type(main_command_set=WCommandPrioritizedSelector)
		def __init__(self, main_command_set, kit_context, default_priority=30):
			WCommandPrioritizedSelector.__init__(self, default_priority=default_priority)

			if isinstance(kit_context, WBrokerCommandManager.MainKitContext) is False:
				raise TypeError('Invalid kit context type')

			self.__main_command_set = main_command_set
			self.__kit_context = kit_context.value
			self.__kits = []
			self.__total_commands = 0

			kit_context_help_cmd = WBrokerCommandManager.BrokerHelpCommand(
				'mako::com.binblob.wasp-launcher.broker::help::context_help.mako',
				template_context={'broker_adapter': self}
			)

			self.add_prioritized(WBrokerCommandManager.BrokerContextCommand(self.__kit_context), 10)
			self.add_prioritized(kit_context_help_cmd, 50)
			self.add_prioritized(WBrokerCommandManager.HelpCommandAlias(self), 50)
			self.add_prioritized(WBrokerCommandManager.UnknownHelpCommand(), 70)

			reduce_command = WReduceCommand(self, self.__kit_context)
			main_context_adapter = WBrokerCommandManager.BrokerContextAdapter(WContext(self.__kit_context))
			main_context_command = WCommandContext(reduce_command, main_context_adapter)

			self.__main_command_set.add_prioritized(main_context_command, 20)
			self.__main_command_set.add_prioritized(reduce_command, 30)

		def kit_context(self):
			return self.__kit_context

		def kits(self):
			return self.__kits

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

			app_commands = WCommandPrioritizedSelector()
			for command in commands:
				app_commands.add(command)

				specific_command_help = WTemplateBrokerCommand(
					'mako::com.binblob.wasp-launcher.broker::help::command_help.mako',
					'help', command.command_token(),
					template_context={'command': command}
				)

				app_commands.add_prioritized(specific_command_help, 60)

			specific_kit_context_help_cmd = WBrokerCommandManager.BrokerHelpCommand(
				'mako::com.binblob.wasp-launcher.broker::help::kit_help.mako',
				template_context={
					'kit_context': self.kit_context(),
					'kit_name': command_kit.name(),
					'kit_commands': commands
				}
			)
			app_commands.add_prioritized(specific_kit_context_help_cmd, 40)
			app_commands.add_prioritized(WBrokerCommandManager.HelpCommandAlias(self), 50)
			app_commands.add_prioritized(
				WBrokerCommandManager.BrokerContextCommand(self.kit_context(), kit_name), 10
			)
			app_commands.add_prioritized(WBrokerCommandManager.UnknownHelpCommand(), 80)

			app_context_adapter = WBrokerCommandManager.BrokerContextAdapter(
				WContext(kit_name, linked_context=WContext(self.kit_context()))
			)
			app_context_command = WCommandContext(
				WReduceCommand(app_commands, *kit_names), app_context_adapter
			)

			self.__main_command_set.add_prioritized(app_context_command, 20)
			self.add_prioritized(WReduceCommand(app_commands, *kit_names), 30)

	def __init__(self):
		self.__internal_set = WBrokerInternalCommandSet()
		self.__kit_context_storage = {}

		internal_command_set = self.__internal_set.commands()
		for kit_context in WBrokerCommandManager.MainKitContext:
			self.__kit_context_storage[kit_context] = WBrokerCommandManager.BrokerCommandSet(
				internal_command_set, kit_context
			)

		root_context_help_cmd = WBrokerCommandManager.BrokerHelpCommand(
			'mako::com.binblob.wasp-launcher.broker::help::root_help.mako',
			template_context={
				'all_kit_context': map(lambda x: x.value, WBrokerCommandManager.MainKitContext)}
		)
		self.__internal_set.commands().add_prioritized(root_context_help_cmd, 50)
		self.__internal_set.commands().add_prioritized(
			WBrokerCommandManager.HelpCommandAlias(internal_command_set), 50
		)
		self.__internal_set.commands().add_prioritized(WBrokerCommandManager.UnknownHelpCommand(), 60)

	def commands_count(self, kit_context=None):
		if kit_context is not None:
			return self.__kit_context_storage[kit_context].total_commands()
		result = 0
		for context_iter in WBrokerCommandManager.MainKitContext:
			if context_iter in self.__kit_context_storage:
				result += self.__kit_context_storage[context_iter].total_commands()
		return result

	@verify_type(command_kit=WCommandKit)
	def add_kit(self, command_kit):
		kit_context = command_kit.kit_context()
		kit_context = self.__kit_context_storage[WBrokerCommandManager.MainKitContext(kit_context)]
		kit_context.add_commands(command_kit)

	# noinspection PyBroadException
	@verify_type('paranoid', command_tokens=str, command_context=(WContextProto, None))
	def exec_broker_command(self, *command_tokens, **command_env):
		command_obj = self.__internal_set.commands().select(*command_tokens, **command_env)

		if command_obj is None:
			return WPlainCommandResult.error('No suitable command found')

		try:
			return command_obj.exec(*command_tokens, **command_env)
		except Exception as e:
			return WExceptionResult('Command execution error', e, traceback.format_exc())
