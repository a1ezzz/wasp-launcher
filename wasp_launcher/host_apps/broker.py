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
import traceback
from abc import abstractmethod

from wasp_general.verify import verify_type
from wasp_general.task.thread import WThreadTask
from wasp_general.network.service import WZMQHandler, WZMQService, WLoglessIOLoop, WZMQSyncAgent

from wasp_general.network.messenger.onion import WMessengerOnion
from wasp_general.network.messenger.session import WMessengerOnionSessionFlow, WMessengerOnionSession
from wasp_general.network.messenger.proto import WMessengerOnionSessionFlowProto, WMessengerOnionLayerProto
from wasp_general.network.messenger.proto import WMessengerEnvelopeProto, WMessengerOnionSessionProto
from wasp_general.network.messenger.layers import WMessengerOnionPackerLayerProto, WMessengerOnionCoderLayerProto
from wasp_general.network.messenger.envelope import WMessengerBytesEnvelope, WMessengerEnvelope

from wasp_general.command.command import WCommandResult
from wasp_general.command.context import WContextProto, WContext, WCommandContextResult, WCommandContextSet
from wasp_general.command.context import WCommandContext

from wasp_launcher.apps import WSyncHostApp, WAppsGlobals, WBrokerCommands


class WManagementCommandPackerLayer(WMessengerOnionPackerLayerProto):
	__layer_name__ = "com.binblob.wasp-launcher.broker-management-command-packer"
	""" Layer name
	"""

	def __init__(self):
		""" Construct new layer
		"""
		WMessengerOnionPackerLayerProto.__init__(
			self, WManagementCommandPackerLayer.__layer_name__
		)

	class Command:
		tokens = []
		context = None

		@staticmethod
		@verify_type(command_tokens=str, request_context=(WContextProto, None))
		def create(*command_tokens, request_context=None):
			command = WManagementCommandPackerLayer.Command()
			command.tokens = list(command_tokens)
			command.context = request_context
			return command

	@verify_type(envelope=WMessengerEnvelopeProto, session=WMessengerOnionSessionProto)
	def pack(self, envelope, session, command=None, **kwargs):
		if command is None:
			raise ValueError("'command parameter must be defined for this layer")

		if isinstance(command, WManagementCommandPackerLayer.Command) is False:
			raise TypeError("Invalid type for 'command' parameter")

		return WMessengerEnvelope({
			'tokens': command.tokens,
			'context': None if command.context is None else WContext.export_context(command.context)
		}, meta=envelope)

	@verify_type(envelope=WMessengerEnvelopeProto, session=WMessengerOnionSessionProto)
	def unpack(self, envelope, session, **kwargs):
		command = envelope.message()
		if isinstance(command, dict) is False:
			raise TypeError('Invalid envelope message type')

		for attr_name in ['tokens', 'context']:
			if attr_name not in command.keys():
				raise ValueError("No '%s' attribute for command envelope" % attr_name)

		return WMessengerEnvelope(
			WManagementCommandPackerLayer.Command.create(
				*(command['tokens']), request_context=WContext.import_context(command['context'])
			), meta=envelope.meta()
		)


class WManagementResultPackerLayer(WMessengerOnionPackerLayerProto):
	__layer_name__ = "com.binblob.wasp-launcher.broker-management-result-packer"
	""" Layer name
	"""

	def __init__(self):
		""" Construct new layer
		"""
		WMessengerOnionPackerLayerProto.__init__(
			self, WManagementResultPackerLayer.__layer_name__
		)

	@verify_type(envelope=WMessengerEnvelopeProto, session=WMessengerOnionSessionProto)
	def pack(self, envelope, session, **kwargs):

		command_result = envelope.message()
		if isinstance(command_result, WCommandResult) is False:
			raise TypeError('Invalid envelope message type')

		result = {
			'output': command_result.output,
			'error': command_result.error,
			'context_mode': False,
			'context': None
		}

		if isinstance(command_result, WCommandContextResult):
			result['context_mode'] = True
			if command_result.context is not None:
				result['context'] = WContext.export_context(command_result.context)

		return WMessengerEnvelope(result, meta=envelope)

	@verify_type(envelope=WMessengerEnvelopeProto, session=WMessengerOnionSessionProto)
	def unpack(self, envelope, session, **kwargs):
		result_dict = envelope.message()
		if isinstance(result_dict, dict) is False:
			raise TypeError('Invalid envelope message type')

		for attr_name in ['output', 'error', 'context_mode', 'context']:
			if attr_name not in result_dict.keys():
				raise ValueError("No '%s' attribute for result envelope" % attr_name)

		if result_dict['context_mode'] is True:
			result_obj = WCommandContextResult(
				output=result_dict['output'], error=result_dict['error'],
				context=WContext.import_context(result_dict['context'])
			)
		else:
			result_obj = WCommandResult(output=result_dict['output'], error=result_dict['error'])

		return WMessengerEnvelope(result_obj, meta=envelope)


class WBrokerClientTask(WZMQService, WThreadTask):

	@verify_type(connection=str)
	def __init__(self, connection):
		setup_agent = WZMQHandler.ConnectSetupAgent(zmq.REQ, connection)

		timeout = WAppsGlobals.config.getint(
			'wasp-launcher::broker::connection::cli', 'command_timeout'
		)

		self.__receive_agent = WZMQSyncAgent(timeout=timeout)
		self.__send_agent = WZMQHandler.SendAgent()

		WZMQService.__init__(self, setup_agent, receive_agent=self.__receive_agent)
		WThreadTask.__init__(self)

	def receive_agent(self):
		return self.__receive_agent

	def send_agent(self):
		return self.__send_agent


class WLauncherBrokerBasicTask(WThreadTask):

	class ManagementProcessingLayer(WMessengerOnionLayerProto):

		__layer_name__ = "com.binblob.wasp-launcher.broker-management-processing-layer"
		""" Layer name
		"""

		def __init__(self):
			WMessengerOnionLayerProto.__init__(
				self, WLauncherBrokerBasicTask.ManagementProcessingLayer.__layer_name__
			)

		@verify_type(envelope=WMessengerEnvelopeProto, session=WMessengerOnionSessionProto)
		def process(self, envelope, session, **kwargs):
			return WMessengerEnvelope(WAppsGlobals.broker_commands.exec_mgmt_command(envelope.message()))

	class ReceiveAgent(WZMQHandler.ReceiveAgent):

		def __init__(self):
			WZMQHandler.ReceiveAgent.__init__(self)
			self.__onion = WMessengerOnion()
			self.__onion.add_layers(
				WLauncherBrokerBasicTask.ManagementProcessingLayer(),
				WManagementCommandPackerLayer(), WManagementResultPackerLayer()
			)
			self.__send_agent = WZMQHandler.SendAgent()

		def on_receive(self, handler, msg):
			session_flow = WMessengerOnionSessionFlow.sequence_flow(
				WMessengerOnionSessionFlowProto.IteratorInfo(
					'com.binblob.wasp-general.encoding-layer',
					mode=WMessengerOnionCoderLayerProto.Mode.decode
				),
				WMessengerOnionSessionFlowProto.IteratorInfo(
					'com.binblob.wasp-general.json-packer-layer',
					mode=WMessengerOnionPackerLayerProto.Mode.unpack
				),
				WMessengerOnionSessionFlowProto.IteratorInfo(
					'com.binblob.wasp-launcher.broker-management-command-packer',
					mode=WMessengerOnionPackerLayerProto.Mode.unpack
				),
				WMessengerOnionSessionFlowProto.IteratorInfo(
					'com.binblob.wasp-launcher.broker-management-processing-layer',
				),
				WMessengerOnionSessionFlowProto.IteratorInfo(
					'com.binblob.wasp-launcher.broker-management-result-packer',
					mode=WMessengerOnionPackerLayerProto.Mode.pack
				),
				WMessengerOnionSessionFlowProto.IteratorInfo(
					'com.binblob.wasp-general.json-packer-layer',
					mode=WMessengerOnionPackerLayerProto.Mode.pack
				),
				WMessengerOnionSessionFlowProto.IteratorInfo(
					'com.binblob.wasp-general.encoding-layer',
					mode=WMessengerOnionCoderLayerProto.Mode.encode
				),
				WMessengerOnionSessionFlowProto.IteratorInfo(
					'com.binblob.wasp-general.send-agent-layer',
					send_agent=self.__send_agent, handler=handler
				)
			)

			session = WMessengerOnionSession(self.__onion, session_flow)
			session.process(WMessengerBytesEnvelope(b''.join(msg)))

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


class WBrokerManagementCommands(WCommandContextSet):

	@verify_type(command=WManagementCommandPackerLayer.Command)
	def exec_mgmt_command(self, command):
		command_obj = self.commands().select(*command.tokens, request_context=command.context)
		if command_obj is None:
			return WCommandResult(error='No suitable command found')

		try:
			if isinstance(command_obj, WCommandContext) is True:
				result = command_obj.exec_context(*command.tokens, request_context=command.context)
			else:
				result = command_obj.exec(*command.tokens)
			return result

		except Exception:
			return WCommandResult(error='Command execution error. Traceback\n%s' % traceback.format_exc())


class WBrokerHostApp(WSyncHostApp):

	__registry_tag__ = 'com.binblob.wasp-launcher.host-app.broker'

	__dependency__ = [
		'com.binblob.wasp-launcher.host-app.guest-apps'
	]

	__broker_tcp_task__ = None
	__broker_ipc_task__ = None

	def start(self):

		self.setup_commands()

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

		WAppsGlobals.broker_commands = None

	def setup_commands(self):
		WAppsGlobals.broker_commands = WBrokerManagementCommands()

		WAppsGlobals.log.info('Populating broker with commands')

		total_commands = 0
		for app in WAppsGlobals.started_apps:
			if issubclass(app, WBrokerCommands) is True:
				has_commands = False
				for command in app.commands():
					WAppsGlobals.broker_commands.commands().add(command)
					has_commands = True
					total_commands += 1

				if has_commands is True:
					WAppsGlobals.log.info(
						'Broker extended by the "%s" application commands' % app.name()
					)
				else:
					WAppsGlobals.log.info(
						'No commands was specified by the guest application: %s' % app.name()
					)

		if total_commands == 0:
			WAppsGlobals.log.warn('No commands was set for the broker')
		else:
			WAppsGlobals.log.info('Loaded broker commands: %i' % total_commands)
