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

from wasp_general.command.result import WPlainCommandResult

from wasp_launcher.core import WAppsGlobals
from wasp_launcher.core_broker import WCommandKit, WTemplateBrokerCommand


class WSchedulerCommandKit(WCommandKit):

	__registry_tag__ = 'com.binblob.wasp-launcher.broker.kits.scheduler'

	class SchedulerInstances(WTemplateBrokerCommand):

		def __init__(self):
			WTemplateBrokerCommand.__init__(
				self,
				'mako::com.binblob.wasp-launcher.broker::scheduler::instances.mako',
				'instances',
				template_context={}
			)

		def result_template(self, *command_tokens, **command_env):
			if WAppsGlobals.scheduler is None:
				return WPlainCommandResult.error('Scheduler collection was not loaded')
			result = WTemplateBrokerCommand.result_template(self, *command_tokens, **command_env)
			result.update_context(scheduler=WAppsGlobals.scheduler)
			return result

		@classmethod
		def brief_description(cls):
			return 'show started scheduler instances'

	class TaskSources(WTemplateBrokerCommand):

		def __init__(self):
			WTemplateBrokerCommand.__init__(
				self,
				'mako::com.binblob.wasp-launcher.broker::scheduler::sources.mako',
				'sources',
				template_context={}
			)

		def result_template(self, *command_tokens, **command_env):
			if WAppsGlobals.scheduler is None:
				return WPlainCommandResult.error('Scheduler was not loaded')
			result = WTemplateBrokerCommand.result_template(self, *command_tokens, **command_env)
			result.update_context(scheduler=WAppsGlobals.scheduler)
			return result

		@classmethod
		def brief_description(cls):
			return 'show tasks sources information'

	class RunningTasksCommand(WTemplateBrokerCommand):

		def __init__(self):
			WTemplateBrokerCommand.__init__(
				self,
				'mako::com.binblob.wasp-launcher.broker::scheduler::running.mako',
				'running_tasks',
				template_context={}
			)

		def result_template(self, *command_tokens, **command_env):
			if WAppsGlobals.scheduler is None:
				return WPlainCommandResult.error('Scheduler was not loaded')
			result = WTemplateBrokerCommand.result_template(self, *command_tokens, **command_env)
			result.update_context(scheduler=WAppsGlobals.scheduler)
			return result

		@classmethod
		def brief_description(cls):
			return 'show tasks that run at the moment'

	class HistoryCommand(WTemplateBrokerCommand):

		def __init__(self):
			WTemplateBrokerCommand.__init__(
				self,
				'mako::com.binblob.wasp-launcher.broker::scheduler::history.mako',
				'history',
				template_context={}
			)

		def result_template(self, *command_tokens, **command_env):
			if WAppsGlobals.scheduler_history is None:
				return WPlainCommandResult.error('Scheduler history is not available')
			result = WTemplateBrokerCommand.result_template(self, *command_tokens, **command_env)
			result.update_context(history_records=WAppsGlobals.scheduler_history)
			return result

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
			WSchedulerCommandKit.RunningTasksCommand(),
			WSchedulerCommandKit.HistoryCommand()
		]
