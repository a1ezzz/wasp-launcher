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
from wasp_general.config import WConfig
from wasp_general.task.thread import WThreadTask
from wasp_general.network.service import WZMQBindHandler, WZMQConnectHandler, WZMQService

from wasp_launcher.host_apps.registry import WLauncherTask
from wasp_launcher.host_apps.globals import WLauncherGlobals


class WRemoteControlClientHandler(WZMQConnectHandler):

	def on_recv(self, msg):
		print('RESPONSE: ' + str(msg))
		pass

	def setup_handler(self, io_loop):
		WZMQConnectHandler.setup_handler(self, io_loop)
		self.stream().send(b'QUERY')
		self.stream().flush()


class WBrokerClientTask(WZMQService, WThreadTask):

	@verify_type(connection=str)
	def __init__(self, connection):
		WZMQService.__init__(self, zmq.REQ, connection, WRemoteControlClientHandler)
		WThreadTask.__init__(self)


class WRemoteControlServerHandler(WZMQBindHandler):

	def on_recv(self, msg):
		print('REQUEST: ' + str(msg))
		self.stream().send(b'STREAM RESPONSE')
		self.stream().flush()


class WLauncherBrokerBasicTask(WThreadTask):

	__messenger_section_prefix__ = 'wasp-launcher::messenger'
	__messenger_general_section__ = 'general'
	__messenger_subsections__ = ['connection', 'tunnel', 'auth', 'auth::static', 'auth::pk']
	__messenger_specific_section__ = None

	__service__ = None

	@classmethod
	def __merge_configuration(cls, config, general_section, specific_section):
		config.add_section(specific_section)
		config.merge_section(WLauncherGlobals.config, specific_section, section_from=general_section)
		config.merge_section(WLauncherGlobals.config, specific_section)

	@classmethod
	def config(cls):
		config = WConfig()

		for subsection in cls.__messenger_subsections__:

			general_section = '%s::%s::%s' % (
				cls.__messenger_section_prefix__, cls.__messenger_general_section__, subsection
			)
			specific_section = '%s::%s::%s' % (
				cls.__messenger_section_prefix__, cls.__messenger_specific_section__, subsection
			)

			cls.__merge_configuration(config, general_section, specific_section)

		return config

	def start(self):
		if self.__service__ is None:
			self.__service__ = self.service()
			self.__service__.start()

	def stop(self):
		if self.__service__ is not None:
			self.__service__.stop()
			self.__service__ = None

	@abstractmethod
	def service(self):
		raise NotImplementedError('This method is abstract')


class WLauncherRemoteControlTask(WLauncherBrokerBasicTask):

	__messenger_specific_section__ = 'remote_control'


class WLauncherTCPRemoteControlTask(WLauncherRemoteControlTask):

	def service(self):
		config = self.config()

		bind_address = config['wasp-launcher::messenger::remote_control::connection']['bind_address']
		if len(bind_address) == 0:
			bind_address = '*'
		port = config.getint('wasp-launcher::messenger::remote_control::connection', 'port')
		connection = 'tcp://%s:%i' % (bind_address, port)

		return WZMQService(zmq.REP, connection, WRemoteControlServerHandler)


class WLauncherIPCRemoteControlTask(WLauncherRemoteControlTask):

	def service(self):
		config = self.config()
		named_socket = config['wasp-launcher::messenger::remote_control::connection']['named_socket_path']
		connection = 'ipc://%s' % named_socket

		return WZMQService(zmq.REP, connection, WRemoteControlServerHandler)


class WLauncherBroker(WLauncherTask):

	__registry_tag__ = 'com.binblob.wasp-launcher.launcher.broker::broker_start'

	__dependency__ = [
		'com.binblob.wasp-launcher.launcher.app_starter::start'
	]

	__remote_control_tcp_task__ = None
	__remote_control_ipc_task__ = None

	def start(self):

		config = WLauncherRemoteControlTask.config()
		tcp_enabled = config.getboolean('wasp-launcher::messenger::remote_control::connection', 'bind')
		ipc_enabled = config.getboolean('wasp-launcher::messenger::remote_control::connection', 'named_socket')

		if WLauncherBroker.__remote_control_tcp_task__ is None and tcp_enabled is True:
			WLauncherBroker.__remote_control_tcp_task__ = WLauncherTCPRemoteControlTask()
			WLauncherBroker.__remote_control_tcp_task__.start()

		if WLauncherBroker.__remote_control_ipc_task__ is None and ipc_enabled is True:
			WLauncherBroker.__remote_control_ipc_task__ = WLauncherIPCRemoteControlTask()
			WLauncherBroker.__remote_control_ipc_task__.start()

	def stop(self):
		if WLauncherBroker.__remote_control_tcp_task__ is not None:
			WLauncherBroker.__remote_control_tcp_task__.stop()
			WLauncherBroker.__remote_control_tcp_task__ = None

		if WLauncherBroker.__remote_control_ipc_task__ is not None:
			WLauncherBroker.__remote_control_ipc_task__.stop()
			WLauncherBroker.__remote_control_ipc_task__ = None
