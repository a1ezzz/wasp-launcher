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
from wasp_general.cli.formatter import WConsoleTableFormatter, na_formatter, local_datetime_formatter
from wasp_general.task.thread_tracker import WTrackerEvents

from wasp_launcher.core import WAppsGlobals


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
	- calls [last|selected|uid] <command> - interact with the specified task (for now only 'stop' command is
available) 
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

	class CallsListCommand(WCommandProto):

		def __init__(self):
			WCommandProto.__init__(self)

		@verify_type(command_tokens=str)
		def match(self, *command_tokens, **command_env):
			if command_tokens == ('calls',):
				return True
			return False

		@verify_type('paranoid', command_tokens=str)
		@verify_type(broker_last_task=(str, None), broker_selected_task=(str, None))
		def exec(self, *command_tokens, broker_last_task=None, broker_selected_task=None, **command_env):
			if self.match(*command_tokens, **command_env) is False:
				raise RuntimeError('Invalid tokens')

			if WAppsGlobals.broker_calls is None:
				return WCommandResult(output='Unable to get task list. Service unavailable', error=1)

			uids = WAppsGlobals.broker_calls.fetch_uids()

			table_formatter = WConsoleTableFormatter('Task uid')
			for uid in uids:
				table_formatter.add_row(uid)

			header = 'Last task: %s\n' % na_formatter(broker_last_task)
			header += 'Selected task: %s\n' % na_formatter(broker_selected_task)
			header += 'Total tasks: %i\n' % len(uids)
			return WCommandResult(output=header + table_formatter.format())

	class CallsSelectCommand(WCommandProto):

		def __init__(self):
			WCommandProto.__init__(self)

		@verify_type(command_tokens=str)
		def match(self, *command_tokens, **command_env):
			if len(command_tokens) == 3 and command_tokens[:2] == ('calls', 'select'):
				if WAppsGlobals.broker_calls is not None:
					return command_tokens[2] in WAppsGlobals.broker_calls.fetch_uids()
			return False

		@verify_type('paranoid', command_tokens=str)
		def exec(self, *command_tokens, **command_env):
			if self.match(*command_tokens, **command_env) is False:
				raise RuntimeError('Invalid tokens')
			uid = command_tokens[2]
			return WCommandResult(
				output='Task "%s" was selected' % uid, broker_selected_task=uid
			)

	class CallsCommand(WCommandProto):

		def __init__(self):
			WCommandProto.__init__(self)
			self.__commands = {
				None: self.__details,
				'stop': self.__stop
			}

		@verify_type(command_tokens=str)
		def match(self, *command_tokens, **command_env):
			if len(command_tokens) >= 2 and command_tokens[0] == 'calls':
				if WAppsGlobals.broker_calls is not None:
					if command_tokens[1] != 'select':
						if len(command_tokens) == 2:
							return True
						return command_tokens[2] in self.__commands.keys()
			return False

		@verify_type('paranoid', command_tokens=str)
		@verify_type(broker_last_task=(str, None), broker_selected_task=(str, None))
		def exec(self, *command_tokens, broker_last_task=None, broker_selected_task=None, **command_env):
			if self.match(*command_tokens, **command_env) is False:
				raise RuntimeError('Invalid tokens')

			uid = command_tokens[1]
			if uid == 'last':
				uid = broker_last_task
			elif uid == 'selected':
				uid = broker_selected_task

			try:
				scheduler_name = WAppsGlobals.broker_calls.get_scheduler(uid)
			except ValueError:
				return WCommandResult(
					output='Invalid task "%s" selected. Type "help calls" for help information',
					error=1
				)

			header = 'Task with uid "%s" selected.\n' % uid

			scheduler = WAppsGlobals.scheduler.instance(scheduler_name)
			if scheduler is None:
				return WCommandResult(
					output=header + 'Invalid task "%s" selected. Unable to find scheduler '
					'instance. Type "help calls" for help information' % uid,
					error=1
				)

			task = None
			for running_record in scheduler.running_records():
				if running_record.task_uid() == uid:
					task = running_record.task()
					break

			if task is None:

				if len(command_tokens) > 2:
					header += 'Unable to submit command "%s" ' % command_tokens[2]
					header += 'to the task for the following reason.\n'

				history_record = WAppsGlobals.scheduler_history.last_record(uid)
				if history_record is None:
					return WCommandResult(
						output=header + 'Task have not been processed by a scheduler yet. '
						'Please wait and call this command again'
					)

				record_type = history_record.record_type
				record_date = local_datetime_formatter(history_record.registered_at)

				if record_type == WTrackerEvents.start:
					return WCommandResult(
						output=header + 'Task was started at %s. Please wait and call this '
						'command again for detailed information' % record_date
					)
				elif record_type == WTrackerEvents.stop:
					return WCommandResult(
						output=header + 'Task was completed and stopped at %s' % record_date
					)
				elif record_type == WTrackerEvents.termination:
					return WCommandResult(
						output=header + 'Task was terminated at %s (Task may be incomplete)' %
						record_date
					)
				elif record_type == WTrackerEvents.exception:
					output = 'Task completion was terminated by an exception at %s.\n' % record_date
					output += 'Exception information: %s\n' % str(history_record.exception)
					output += history_record.exception_details

					return WCommandResult(output=header + output)
				elif record_type == WTrackerEvents.wait:
					return WCommandResult(
						output=header + 'Task was not started and have been postponed at %s. '
						'Please wait and call this command again' % record_date
					)
				elif record_type == WTrackerEvents.drop:
					return WCommandResult(
						output=header + 'Task was not started and have been drop by a scheduler '
						'at %s. If you want to start this task again - call task command again'
					)
				raise RuntimeError('Invalid history record type spotted: %s' % str(record_type))

			command_key = command_tokens[2] if len(command_tokens) > 2 else None

			return self.__commands[command_key](uid, task, scheduler_name)

		@classmethod
		def __details(cls, task_uid, task, scheduler_name):
			output = 'Task with uid "%s" selected.\n' % task_uid
			output += 'Task was registered on scheduler: %s\n' % na_formatter(
				scheduler_name, none_value='<default instance>'
			)

			event_record = WAppsGlobals.scheduler_history.last_record(
				task_uid, WTrackerEvents.start, WTrackerEvents.wait, WTrackerEvents.drop
			)
			if event_record is not None:
				record_date = local_datetime_formatter(event_record.registered_at)

				if event_record.record_type == WTrackerEvents.drop:
					output += 'Task was dropped at %s\n' % record_date
				elif event_record.record_type == WTrackerEvents.wait:
					output += 'Task has been waited since %s\n' % record_date
				elif event_record.record_type == WTrackerEvents.start:
					output += 'Task has been started at %s\n' % record_date

			task_status = task.state_details()
			if task_status is not None:
				output += '\n' + task_status

			return WCommandResult(output=output)

		@classmethod
		def __stop(cls, task_uid, task, scheduler_name):
			header = 'Task with uid "%s" selected.\n' % task_uid
			task.stop()
			return WCommandResult(output=header + 'Task was requested to stop')

	def __init__(self):
		WCommandSet.__init__(self, command_selector=WCommandPrioritizedSelector())
		self.commands().add_prioritized(WBrokerInternalCommandSet.DoubleDotCommand(), 10)
		self.commands().add_prioritized(WBrokerInternalCommandSet.DotCommand(), 10)
		self.commands().add_prioritized(WBrokerInternalCommandSet.GeneralUsageHelpCommand(), 10)
		self.commands().add_prioritized(WBrokerInternalCommandSet.CallsListCommand(), 10)
		self.commands().add_prioritized(WBrokerInternalCommandSet.CallsSelectCommand(), 10)
		self.commands().add_prioritized(WBrokerInternalCommandSet.CallsCommand(), 10)
