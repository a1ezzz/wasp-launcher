# -*- coding: utf-8 -*-
# wasp_launcher/wasp_launcher/apps/broker/internal_commands.py
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

from wasp_general.command.command import WCommandSet, WCommandPrioritizedSelector, WCommand, WCommandResult
from wasp_general.command.command import WCommandProto
from wasp_general.command.context import WContextProto


class WBrokerInternalCommandSet(WCommandSet):

	__help_info__ = {
		'.': 'This command allows to switch current context to main context',
		'..': 'This command allows to switch current context to one level higher context',
		'exit': 'Terminate this session and close the client',
		'calls': """This command allows to interact with some long running tasks (not all of them are capable \
to, but most they are). You can address single task by its uid or by special words like 'last' and 'selected'. \
By calling a 'last' task you will address long running task, that was invoked last time. 'last' task is changed every \
time you invoke a new task. You can also set a single task as a 'selected' and address it every time you want. Only \
one task can be selected at a single moment. 

You can interact with these tasks by the following way:

	- calls - list of all available interactive tasks
	- calls select [uid] - mark task that has the specified uid as selected
	- calls [last|selected|uid] <command> - interact with the specified task
""",
		'help': """It is a help system. It can be used in any context and for any command. It can be \
called directly for particular help section like:
	- help <[core|apps] <[module name or alias] <command>>>
	- help [internal-command]
	- [core|apps] help
	- [core|apps] [module name or alias] help
	- [core|apps] [module name or alias] help [command]

Or it can be called inside a context by calling 'help', in that case - result will be different for different context

You can change current context by calling a command:
	- [core|apps] <[module name or alias]>

You can call a specific command in any context by the following pattern:
	- [core|apps] [module or alias] [command] <command_arg1> <command_arg2...>

There are several predefined (internal) commands that are available everywhere no matter what context is selected at \
the moment. Here they are:
	- . (dot) - switch current context to main context
	- .. (double dot) - switch current context to one level higher
	- calls - work with long running tasks (for detailed help information - type "help calls")
	- help - this help information
	- exit|quit - terminate this session and close the client
"""
	}

	class DoubleDotCommand(WCommand):

		def __init__(self):
			WCommand.__init__(self, '..')

		@verify_type('paranoid', command_tokens=str)
		@verify_type(command_context=(WContextProto, None))
		def _exec(self, *command_tokens, command_context=None, **command_env):
			if command_context is not None:
				return WCommandResult(command_context=command_context.linked_context())
			return WCommandResult(command_context=None)

	class DotCommand(WCommand):

		def __init__(self):
			WCommand.__init__(self, '.')

		@verify_type('paranoid', command_tokens=str, command_context=(WContextProto, None))
		def _exec(self, *command_tokens, command_context=None, **command_env):
			return WCommandResult(command_context=None)

	class GeneralUsageHelpCommand(WCommandProto):

		def __init__(self):
			WCommandProto.__init__(self)

		@verify_type(command_tokens=str)
		def match(self, *command_tokens, **command_env):
			if len(command_tokens) == 2 and command_tokens[0] == 'help':
				if command_tokens[1] in WBrokerInternalCommandSet.__help_info__.keys():
					return True
			return False

		@verify_type('paranoid', command_tokens=str)
		def exec(self, *command_tokens, **command_env):
			if self.match(*command_tokens, **command_env) is False:
				raise RuntimeError('Invalid tokens')
			return WCommandResult(output=WBrokerInternalCommandSet.__help_info__[command_tokens[1]])

	def __init__(self):
		WCommandSet.__init__(self, command_selector=WCommandPrioritizedSelector())
		self.commands().add_prioritized(WBrokerInternalCommandSet.DoubleDotCommand(), 10)
		self.commands().add_prioritized(WBrokerInternalCommandSet.DotCommand(), 10)
		self.commands().add_prioritized(WBrokerInternalCommandSet.GeneralUsageHelpCommand(), 10)
