# -*- coding: utf-8 -*-
# wasp_launcher/broker_commands.py
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

from wasp_general.verify import verify_type, verify_value

from wasp_general.command.command import WCommandResult, WCommandProto, WCommand, WReduceCommand
from wasp_general.command.command import WCommandPrioritizedSelector
from wasp_general.command.context import WContextProto, WContext, WCommandContextResult, WCommandContextAdapter
from wasp_general.command.context import WCommandContext, WCommandContextSet

from wasp_launcher.apps import WAppsGlobals, WGuestAppCommandKit, WHostAppRegistry, WHostAppCommandKit


class WBrokerCommandManager:

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
		@verify_value(main_context=lambda x: len(x) > 0)
		def __init__(self, main_command_set, main_context, default_priority=30):
			WCommandPrioritizedSelector.__init__(self, default_priority=default_priority)
			self.__main_command_set = main_command_set
			self.__main_context = main_context

			self.add_prioritized(WBrokerCommandManager.BrokerContextCommand(self.__main_context), 10)

			reduce_command = WReduceCommand(self, self.__main_context)
			main_context_adapter = WBrokerCommandManager.BrokerContextAdapter(WContext(self.__main_context))
			main_context_command = WCommandContext(reduce_command, main_context_adapter)

			self.__main_command_set.add_prioritized(main_context_command, 20)
			self.__main_command_set.add_prioritized(reduce_command, 30)

		@verify_type(context_name=str, commands=WCommandProto, force_context_command=bool, alias=(str, None))
		@verify_value(context_name=lambda x: len(x) > 0, alias=lambda x: x is None or len(x) > 0)
		def add_commands(self, context_name, *commands, force_context_command=False, alias=None):
			if force_context_command is True or len(commands) > 0:
				app_names = (context_name,) if alias is None else (context_name, alias)
				app_commands = WCommandPrioritizedSelector()
				app_commands.add_prioritized(
					WBrokerCommandManager.BrokerContextCommand(self.__main_context, context_name),
					10
				)

				for command in commands:
					app_commands.add(command)

				app_context_adapter = WBrokerCommandManager.BrokerContextAdapter(
					WContext(context_name, linked_context=WContext(self.__main_context))
				)
				app_context_command = WCommandContext(
					WReduceCommand(app_commands, *app_names), app_context_adapter
				)

				self.__main_command_set.add_prioritized(app_context_command, 20)
				self.add_prioritized(WReduceCommand(app_commands, *app_names), 30)

	def __init__(self):
		self.__internal_set = WCommandContextSet()
		self.__internal_set.commands().add_prioritized(WBrokerCommandManager.DotCommand(), 10)
		self.__internal_set.commands().add_prioritized(WBrokerCommandManager.DoubleDotCommand(), 10)

		main_command_set = self.__internal_set.commands()
		self.__host_apps_set = WBrokerCommandManager.BrokerCommandSet(main_command_set, 'host-app')
		self.__host_apps_commands = 0
		self.__guest_apps_set = WBrokerCommandManager.BrokerCommandSet(main_command_set, 'guest-app')
		self.__guest_apps_commands = 0

		self.__load_host_apps_kits()

	def host_app_commands(self):
		return self.__host_apps_commands

	def guest_app_commands(self):
		return self.__guest_apps_commands

	def __load_host_apps_kits(self):
		for kit_name in WAppsGlobals.config.split_option('wasp-launcher::broker::kits::host_apps', 'load_kits'):
			host_app = WHostAppRegistry.registry_storage().tasks(kit_name)
			if host_app is None:
				raise RuntimeError('Unable to find suitable host-app kit for "%s"' % kit_name)

			app_name = host_app.name()

			config_alias_section = 'wasp-launcher::broker::kits::host_apps::aliases'
			alias = None
			if WAppsGlobals.config.has_option(config_alias_section, app_name) is True:
				alias = WAppsGlobals.config[config_alias_section][app_name]

			commands = host_app.commands()
			self.__host_apps_set.add_commands(app_name, *commands, alias=alias)
			self.__host_apps_commands += len(commands)

	@verify_type(guest_app=WGuestAppCommandKit)
	def add_guest_app(self, guest_app):
		app_name = guest_app.name()
		alias = None
		if WAppsGlobals.config.has_option('wasp-launcher::broker::kits::guest_apps::aliases', app_name) is True:
			alias = WAppsGlobals.config['wasp-launcher::broker::kits::guest_apps::aliases'][app_name]

		commands = guest_app.commands()
		self.__guest_apps_set.add_commands(app_name, *commands, alias=alias)
		self.__guest_apps_commands += len(commands)

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


class WCoreCommandKit(WHostAppCommandKit):

	__registry_tag__ = 'com.binblob.wasp-launcher.host-app.broker.kits.core'

	class Threads(WCommand):

		def __init__(self):
			WCommand.__init__(self, 'threads')

		@verify_type('paranoid', command_tokens=str)
		def _exec(self, *command_tokens, **command_env):
			threads = threading.enumerate()
			output = 'Total threads: %i' % len(threads)
			if len(threads) > 0:
				output += '\n\tThread name\n\t==========='
				for thread in threads:
					output += '\n\t' + thread.name

			return WCommandResult(output=output)

	@classmethod
	def commands(cls):
		return [WCoreCommandKit.Threads()]


class WModelDBCommandKit(WHostAppCommandKit):

	__registry_tag__ = 'com.binblob.wasp-launcher.host-app.broker.kits.model-db'

	@classmethod
	def commands(cls):
		return []


class WModelObjCommandKit(WHostAppCommandKit):

	__registry_tag__ = 'com.binblob.wasp-launcher.host-app.broker.kits.model-obj'

	@classmethod
	def commands(cls):
		return []


class WGuestCommandKit(WHostAppCommandKit):

	__registry_tag__ = 'com.binblob.wasp-launcher.host-app.broker.kits.guest'

	@classmethod
	def commands(cls):
		return []


class WScheduleCommandKit(WHostAppCommandKit):

	__registry_tag__ = 'com.binblob.wasp-launcher.host-app.broker.kits.schedule'

	@classmethod
	def commands(cls):
		return []
