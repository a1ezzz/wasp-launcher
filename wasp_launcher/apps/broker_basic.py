# -*- coding: utf-8 -*-
# wasp_launcher/apps/broker_basic.py
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
# TODO: write tests for the code

# noinspection PyUnresolvedReferences
from wasp_launcher.version import __author__, __version__, __credits__, __license__, __copyright__, __email__
# noinspection PyUnresolvedReferences
from wasp_launcher.version import __status__

import zmq
from abc import abstractmethod

from wasp_general.verify import verify_type
from wasp_general.network.service import WZMQHandler, WZMQService, WLoglessIOLoop, WZMQSyncAgent

from wasp_general.network.messenger.onion import WMessengerOnion
from wasp_general.network.messenger.session import WMessengerOnionSessionFlow, WMessengerOnionSession
from wasp_general.network.messenger.proto import WMessengerOnionSessionFlowProto, WMessengerOnionLayerProto
from wasp_general.network.messenger.proto import WMessengerEnvelopeProto, WMessengerOnionSessionProto
from wasp_general.network.messenger.layers import WMessengerOnionPackerLayerProto, WMessengerOnionCoderLayerProto
from wasp_general.network.messenger.envelope import WMessengerBytesEnvelope, WMessengerEnvelope

from wasp_general.command.command import WCommandResult, WCommandEnv
from wasp_general.command.context import WContext

from wasp_launcher.core import WAppsGlobals, WThreadedApp


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

	class Command(WCommandEnv):
		serialization_helpers = {'command_context': WContext.ContextSerializationHelper()}

		def __init__(self, *command_tokens, **command_env):
			WCommandEnv.__init__(self, **command_env)
			self.tokens = command_tokens

		def serialize_env(self, **serialization_helpers):
			helpers = serialization_helpers.copy()
			helpers.update(WManagementCommandPackerLayer.Command.serialization_helpers)
			return WCommandEnv.serialize_env(self, **helpers)

		@classmethod
		@verify_type(env=dict)
		def deserialize_env(cls, env, **serialization_helpers):
			helpers = serialization_helpers.copy()
			helpers.update(WManagementCommandPackerLayer.Command.serialization_helpers)
			return WCommandEnv.deserialize_env(env, **helpers)

	@verify_type('paranoid', session=WMessengerOnionSessionProto)
	@verify_type(envelope=WMessengerEnvelopeProto)
	def pack(self, envelope, session, command=None, **kwargs):
		if command is None:
			raise ValueError("'command parameter must be defined for this layer")

		if isinstance(command, WManagementCommandPackerLayer.Command) is False:
			raise TypeError("Invalid type for 'command' parameter")

		return WMessengerEnvelope({'tokens': command.tokens, 'env': command.serialize_env()}, meta=envelope)

	@verify_type('paranoid', session=WMessengerOnionSessionProto)
	@verify_type(envelope=WMessengerEnvelopeProto)
	def unpack(self, envelope, session, **kwargs):
		command = envelope.message()
		if isinstance(command, dict) is False:
			raise TypeError('Invalid envelope message type')

		for attr_name in ['tokens', 'env']:
			if attr_name not in command.keys():
				raise ValueError("No '%s' attribute for command envelope" % attr_name)

		return WMessengerEnvelope(
			WManagementCommandPackerLayer.Command(
				*(command['tokens']),
				**(WManagementCommandPackerLayer.Command.deserialize_env(command['env']))
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
		self.__command_context_helper = WContext.ContextSerializationHelper()

	@verify_type('paranoid', session=WMessengerOnionSessionProto)
	@verify_type(envelope=WMessengerEnvelopeProto)
	def pack(self, envelope, session, **kwargs):

		command_result = envelope.message()
		if isinstance(command_result, WCommandResult) is False:
			raise TypeError('Invalid envelope message type')

		serialized_vars = command_result.serialize_env(command_context=self.__command_context_helper)

		result = {
			'output': command_result.output,
			'error': command_result.error,
			'env': serialized_vars
		}

		return WMessengerEnvelope(result, meta=envelope)

	@verify_type('paranoid', session=WMessengerOnionSessionProto)
	@verify_type(envelope=WMessengerEnvelopeProto)
	def unpack(self, envelope, session, **kwargs):
		result_dict = envelope.message()
		if isinstance(result_dict, dict) is False:
			raise TypeError('Invalid envelope message type')

		for attr_name in ['output', 'error', 'env']:
			if attr_name not in result_dict.keys():
				raise ValueError("No '%s' attribute for result envelope" % attr_name)

		deserialized_vars = WCommandResult.deserialize_env(
			result_dict['env'], command_context=self.__command_context_helper
		)

		result_obj = WCommandResult(
			output=result_dict['output'], error=result_dict['error'], **deserialized_vars
		)

		return WMessengerEnvelope(result_obj, meta=envelope)


class WBrokerClientTask(WZMQService, WThreadedApp):

	@verify_type('paranoid', connection=str)
	def __init__(self, connection):
		setup_agent = WZMQHandler.ConnectSetupAgent(
			zmq.REQ, connection, WZMQHandler.SocketOption(zmq.IMMEDIATE, 1)
		)

		timeout = WAppsGlobals.config.getint(
			'wasp-launcher::broker::connection::cli', 'command_timeout'
		)

		self.__receive_agent = WZMQSyncAgent(timeout=timeout)
		self.__send_agent = WZMQHandler.SendAgent()

		WZMQService.__init__(self, setup_agent, receive_agent=self.__receive_agent)
		WThreadedApp.__init__(self)

	def receive_agent(self):
		return self.__receive_agent

	def send_agent(self):
		return self.__send_agent

	def start(self):
		WThreadedApp.start(self)

	def stop(self):
		WThreadedApp.stop(self)

	def thread_started(self):
		WZMQService.start(self)

	def thread_stopped(self):
		WZMQService.stop(self)


class WLauncherBrokerBasicTask(WThreadedApp):

	class ManagementProcessingLayer(WMessengerOnionLayerProto):

		__layer_name__ = "com.binblob.wasp-launcher.broker-management-processing-layer"
		""" Layer name
		"""

		def __init__(self):
			WMessengerOnionLayerProto.__init__(
				self, WLauncherBrokerBasicTask.ManagementProcessingLayer.__layer_name__
			)

		@verify_type('paranoid', session=WMessengerOnionSessionProto)
		@verify_type(envelope=WMessengerEnvelopeProto)
		def process(self, envelope, session, **kwargs):
			return self.exec(envelope.message())

		@classmethod
		@verify_type(command=WManagementCommandPackerLayer.Command)
		def exec(cls, command):
			return WMessengerEnvelope(
				WAppsGlobals.broker_commands.exec_broker_command(
					*command.tokens, **command.env
				)
			)

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

	def thread_started(self):
		if self.__service__ is None:
			self.__service__ = self.service()
			self.__service__.start()

	def thread_stopped(self):
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
