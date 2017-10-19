# -*- coding: utf-8 -*-
# wasp_launcher/core_scheduler.py
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
# TODO: test the code

# noinspection PyUnresolvedReferences
from wasp_launcher.version import __author__, __version__, __credits__, __license__, __copyright__, __email__
# noinspection PyUnresolvedReferences
from wasp_launcher.version import __status__


from abc import abstractmethod

from wasp_general.task.scheduler.proto import WScheduleTask, WTaskSourceProto
from wasp_general.task.thread_tracker import WThreadTracker, WScheduleRecordTracker
from wasp_general.verify import verify_type, verify_value

from wasp_launcher.core import WSyncApp, WAppsGlobals, WThreadTaskLoggingHandler


class WLauncherScheduleTask(WScheduleTask, WThreadTracker, WThreadTaskLoggingHandler):
	"""
	stopped - to history
	exception raised - to history
	"""

	def __init__(self, thread_join_timeout=None):
		WThreadTracker.__init__(self)
		WScheduleTask.__init__(self, thread_join_timeout=thread_join_timeout)
		WThreadTaskLoggingHandler.__init__(self)

	def uid(self):
		return str(WScheduleTask.uid(self))

	def tracker_storage(self):
		return WAppsGlobals.scheduler_history

	@abstractmethod
	def name(self):
		""" Common name for the same set of tasks

		:return: str
		"""
		raise NotImplementedError('This method is abstract')

	@abstractmethod
	def brief_description(self):
		""" General/brief information about this task. That is used for information user about task purposes

		:return: str
		"""
		raise NotImplementedError('This method is abstract')

	def event_details(self, event):
		""" Return information about the given tracking event

		that may

		:param event:
		:return:
		"""
		return None

	def state_details(self):
		""" Return detailed information about current task state (it is presumed that this information
		is available when task is running only)

		:return: str or None
		"""
		return None

	def thread_stopped(self):
		WThreadTracker.thread_stopped(self)

	def thread_exception(self, raised_exception):
		WThreadTracker.thread_exception(self, raised_exception)
		WThreadTaskLoggingHandler.thread_exception(self, raised_exception)


class WLauncherScheduleRecord(WScheduleRecordTracker):

	@verify_type('paranoid', task_group_id=(str, None))
	@verify_value('paranoid', on_drop=lambda x: x is None or callable(x))
	@verify_value('paranoid', on_wait=lambda x: x is None or callable(x))
	@verify_type(task=WLauncherScheduleTask)
	def __init__(self, task, policy=None, task_group_id=None, on_drop=None, on_wait=None):
		WScheduleRecordTracker.__init__(
			self, task, policy=policy, task_group_id=task_group_id, on_drop=on_drop, on_wait=on_wait,
			track_wait=True, track_drop=True
		)


class WLauncherTaskSource(WTaskSourceProto):

	@abstractmethod
	def name(self):
		raise NotImplementedError('This method is abstract')

	# noinspection PyMethodMayBeStatic
	def description(self):
		return None

	@abstractmethod
	@verify_type(schedule_record=WLauncherScheduleRecord)
	def add_record(self, schedule_record):
		raise NotImplementedError('This method is abstract')


class WSchedulerTaskSourceInstaller(WSyncApp):

	__dependency__ = ['com.binblob.wasp-launcher.apps.scheduler::init']
	__scheduler_instance__ = None
	# default scheduler instance is used by default

	@classmethod
	def config_section(cls):
		return 'wasp-launcher::applications::%s' % cls.name()

	def start(self):
		instance_name = self.scheduler_instance()
		instance = WAppsGlobals.scheduler.instance(instance_name)
		if instance is None:
			WAppsGlobals.log.error(
				'Scheduler instance "%s" not found. Tasks will not be able to start' % instance_name
			)
			return

		for source in self.sources():
			instance.add_task_source(source(instance))

	def stop(self):
		pass

	@abstractmethod
	def sources(self):
		raise NotImplementedError('This method is abstract')

	@classmethod
	def scheduler_instance(cls):
		return cls.__scheduler_instance__
