# -*- coding: utf-8 -*-
# wasp_launcher/host_apps/broker.py
#
# Copyright (C) 2016 the wasp-launcher authors and contributors
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

import zmq
from abc import abstractmethod

from wasp_general.verify import verify_type
from wasp_general.task.thread import WThreadTask
from wasp_general.network.service import WZMQHandler, WZMQService, WLoglessIOLoop, WZMQSyncAgent

from wasp_launcher.apps import WSyncHostApp, WAppsGlobals


class WBrokerClientTask(WZMQService, WThreadTask):

	@verify_type(connection=str)
	def __init__(self, connection):
		setup_agent = WZMQHandler.ConnectSetupAgent(zmq.REQ, connection)

		timeout = WAppsGlobals.config.getint(
			'wasp-launcher::broker::connection::cli', 'command_timeout'
		)

		self.__receive_agent = WZMQSyncAgent(timeout=timeout)

		WZMQService.__init__(self, setup_agent, receive_agent=self.__receive_agent)
		WThreadTask.__init__(self)

	def receive_agent(self):
		return self.__receive_agent


class WLauncherBrokerBasicTask(WThreadTask):

	class ReceiveAgent(WZMQHandler.ReceiveAgent):

		def on_receive(self, handler, msg):
			print('REQUEST: ' + str(msg))
			import json
			msg = json.loads((b''.join(msg)).decode())
			send_agent = WZMQHandler.SendAgent()
			send_agent.send(handler, json.dumps({'response': 'OK', 'request': msg}).encode())


	__service__ = None

	def start(self):
		if self.__service__ is None:
			self.__service__ = self.service()
			self.__service__.start()

	def stop(self):
		if self.__service__ is not None:
			self.__service__.stop()
			self.__service__ = None

	@abstractmethod
	def connection(self):
		raise NotImplementedError('This method is abstract')

	def service(self):
		setup_agent = WZMQHandler.BindSetupAgent(zmq.REP, self.connection())
		receive_agent = WLauncherBrokerBasicTask.ReceiveAgent()

		return WZMQService(setup_agent, loop=WLoglessIOLoop(), receive_agent=receive_agent)


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


class WBrokerHostApp(WSyncHostApp):

	__registry_tag__ = 'com.binblob.wasp-launcher.host-app.broker'

	__dependency__ = [
		'com.binblob.wasp-launcher.host-app.guest-apps'
	]

	__broker_tcp_task__ = None
	__broker_ipc_task__ = None

	def start(self):
		tcp_enabled = WAppsGlobals.config.getboolean('wasp-launcher::broker::connection', 'bind')
		ipc_enabled = WAppsGlobals.config.getboolean('wasp-launcher::broker::connection', 'named_socket')

		if WBrokerHostApp.__broker_tcp_task__ is None and tcp_enabled is True:
			WBrokerHostApp.__broker_tcp_task__ = WLauncherBrokerTCPTask()
			WBrokerHostApp.__broker_tcp_task__.start()

		if WBrokerHostApp.__broker_ipc_task__ is None and ipc_enabled is True:
			WBrokerHostApp.__broker_ipc_task__ = WLauncherBrokerIPCTask()
			WBrokerHostApp.__broker_ipc_task__.start()

	def stop(self):
		if WBrokerHostApp.__broker_tcp_task__ is not None:
			WBrokerHostApp.__broker_tcp_task__.stop()
			WBrokerHostApp.__broker_tcp_task__ = None

		if WBrokerHostApp.__broker_ipc_task__ is not None:
			WBrokerHostApp.__broker_ipc_task__.stop()
			WBrokerHostApp.__broker_ipc_task__ = None
