# -*- coding: utf-8 -*-
# wasp_launcher/apps/broker_app.py
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
from wasp_general.thread import WCriticalResource

from wasp_launcher.core import WSyncApp, WAppsGlobals
from wasp_launcher.core_broker import WCommandKit
from wasp_launcher.apps.broker_basic import WLauncherBrokerBasicTask
from wasp_launcher.apps.broker_commands import WBrokerCommandManager


class WLauncherBrokerTCPTask(WLauncherBrokerBasicTask):

	__thread_name__ = 'Broker-TCP'

	def connection(self):
		bind_address = WAppsGlobals.config['wasp-launcher::broker::connection']['bind_address']
		if len(bind_address) == 0:
			bind_address = '*'
		port = WAppsGlobals.config.getint('wasp-launcher::broker::connection', 'port')
		return 'tcp://%s:%i' % (bind_address, port)


class WLauncherBrokerIPCTask(WLauncherBrokerBasicTask):

	__thread_name__ = 'Broker-IPC'

	def connection(self):
		named_socket = WAppsGlobals.config['wasp-launcher::broker::connection']['named_socket_path']
		return 'ipc://%s' % named_socket


class WBrokerCallsRegistry(WCriticalResource):
	# Task creation latency should be small as possible, so only some checks are made. There is no check
	# if different tasks have the same uid. It may be done outside of this class

	def __init__(self):
		WCriticalResource.__init__(self)
		self.__registry = []

	@verify_type('paranoid', uid=str, scheduler=(str, None))
	def add_task(self, uid, scheduler):
		self.__add_task(uid, scheduler)

	@WCriticalResource.critical_section()
	@verify_type(uid=str, scheduler=(str, None))
	def __add_task(self, uid, scheduler):
		self.__registry.append((uid, scheduler))

	def fetch_uids(self):
		return tuple(map(lambda x: x[0], self))

	@verify_type(uid=str)
	def get_scheduler(self, uid):
		for record in self:
			if record[0] == uid:
				return record[1]
		raise ValueError('Invalid uid is specified')

	def __iter__(self):
		result = self.__clone()
		while len(result) > 0:
			yield result.pop(-1)

	@WCriticalResource.critical_section()
	def __clone(self):
		return self.__registry.copy()


class WBrokerAppTasks:
	__broker_tcp_task__ = None
	__broker_ipc_task__ = None


class WBrokerInitApp(WSyncApp):

	__registry_tag__ = 'com.binblob.wasp-launcher.apps.broker::init'

	__dependency__ = [
		'com.binblob.wasp-launcher.apps.config'
	]

	def start(self):
		WAppsGlobals.log.info('Broker is initializing')

		tcp_enabled = WAppsGlobals.config.getboolean('wasp-launcher::broker::connection', 'bind')
		ipc_enabled = WAppsGlobals.config.getboolean('wasp-launcher::broker::connection', 'named_socket')

		if WBrokerAppTasks.__broker_tcp_task__ is None and tcp_enabled is True:
			WBrokerAppTasks.__broker_tcp_task__ = WLauncherBrokerTCPTask()

		if WBrokerAppTasks.__broker_ipc_task__ is None and ipc_enabled is True:
			WBrokerAppTasks.__broker_ipc_task__ = WLauncherBrokerIPCTask()

		if WAppsGlobals.broker_commands is None:
			WAppsGlobals.broker_commands = WBrokerCommandManager()

		if WAppsGlobals.broker_calls is None:
			WAppsGlobals.broker_calls = WBrokerCallsRegistry()

	def stop(self):
		WAppsGlobals.log.info('Broker is finalizing')
		WBrokerAppTasks.__broker_tcp_task__ = None
		WBrokerAppTasks.__broker_ipc_task__ = None
		WAppsGlobals.broker_commands = None
		WAppsGlobals.broker_calls = None


class WBrokerApp(WSyncApp):

	__registry_tag__ = 'com.binblob.wasp-launcher.apps.broker::start'

	__dependency__ = ['com.binblob.wasp-launcher.apps.broker::init']

	__dynamic_dependency__ = WCommandKit

	def start(self):
		core_commands = WAppsGlobals.broker_commands.commands_count(WBrokerCommandManager.MainSections.core)
		app_commands = WAppsGlobals.broker_commands.commands_count(WBrokerCommandManager.MainSections.apps)

		total_commands = WAppsGlobals.broker_commands.commands_count()
		if total_commands == 0:
			WAppsGlobals.log.warn('No commands was set for the broker')
		else:
			WAppsGlobals.log.info(
				'Loaded broker commands: %i (core: %i, apps: %i)' %
				(total_commands, core_commands, app_commands)
			)

		WAppsGlobals.log.info('Broker is starting')

		if WBrokerAppTasks.__broker_tcp_task__ is not None:
			WBrokerAppTasks.__broker_tcp_task__.start()

		if WBrokerAppTasks.__broker_ipc_task__ is not None:
			WBrokerAppTasks.__broker_ipc_task__.start()

	def stop(self):
		WAppsGlobals.log.info('Broker is stopping')

		if WBrokerAppTasks.__broker_tcp_task__ is not None:
			WBrokerAppTasks.__broker_tcp_task__.stop()

		if WBrokerAppTasks.__broker_ipc_task__ is not None:
			WBrokerAppTasks.__broker_ipc_task__.stop()
