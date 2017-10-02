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


from abc import ABCMeta, abstractmethod

from wasp_general.task.scheduler.proto import WScheduleTask, WTaskSourceProto
from wasp_general.task.thread_tracker import WThreadTracker
from wasp_general.verify import verify_type

from wasp_launcher.core import WSyncApp, WAppsGlobals


class WLauncherScheduleTask(WScheduleTask, WThreadTracker):
	"""
	stopped - to history
	exception raised - to history
	"""

	def __init__(self, thread_join_timeout=None):
		WScheduleTask.__init__(self, thread_join_timeout=thread_join_timeout)
		WThreadTracker.__init__(self)

	def tracker_storage(self):
		return WAppsGlobals.scheduler_history

	@abstractmethod
	def name(self):
		raise NotImplementedError('This method is abstract')

	@abstractmethod
	def description(self):
		raise NotImplementedError('This method is abstract')

	def task_details(self):
		return self.description()


class WLauncherTaskSource(WTaskSourceProto):

	@abstractmethod
	def name(self):
		raise NotImplementedError('This method is abstract')

	# noinspection PyMethodMayBeStatic
	def description(self):
		return None


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
