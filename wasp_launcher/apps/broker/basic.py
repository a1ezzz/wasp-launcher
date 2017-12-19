# -*- coding: utf-8 -*-
# wasp_launcher/apps/broker/basic.py
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
from wasp_general.network.messenger.composer import WMessengerComposerLayer
from wasp_general.network.messenger.envelope import WMessengerBytesEnvelope, WMessengerEnvelope, WMessengerDictEnvelope

from wasp_launcher.apps.broker.composer import WLauncherComposerFactory, WCommandRequest

from wasp_launcher.core import WAppsGlobals, WThreadedApp


class WBrokerClientTask(WZMQService, WThreadedApp):

	@verify_type('paranoid', connection=str)
	def __init__(self, connection):
		# TODO: double check!
		#setup_agent = WZMQHandler.ConnectSetupAgent(
		#	zmq.REQ, connection, WZMQHandler.SocketOption(zmq.IMMEDIATE, 1)
		#)
		setup_agent = WZMQHandler.ConnectSetupAgent(zmq.REQ, connection)

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
		@verify_type(command=WCommandRequest)
		def exec(cls, command):
			return WMessengerEnvelope(
				WAppsGlobals.broker_commands.exec_broker_command(
					*command.command_tokens, **command.command_env
				)
			)

	class ReceiveAgent(WZMQHandler.ReceiveAgent):

		def __init__(self):
			WZMQHandler.ReceiveAgent.__init__(self)
			self.__onion = WMessengerOnion()
			self.__onion.add_layers(WLauncherBrokerBasicTask.ManagementProcessingLayer())
			self.__send_agent = WZMQHandler.SendAgent()
			self.__composer_factory = WLauncherComposerFactory()

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
					"com.binblob.wasp-general.simple-casting-layer",
					from_envelope=WMessengerEnvelope, to_envelope=WMessengerDictEnvelope
				),
				WMessengerOnionSessionFlowProto.IteratorInfo(
					'com.binblob.wasp-general.composer-packer-layer',
					mode=WMessengerComposerLayer.Mode.compose,
					composer_factory=self.__composer_factory
				),

				WMessengerOnionSessionFlowProto.IteratorInfo(
					'com.binblob.wasp-launcher.broker-management-processing-layer',
				),
				WMessengerOnionSessionFlowProto.IteratorInfo(
					'com.binblob.wasp-general.composer-packer-layer',
					mode=WMessengerComposerLayer.Mode.decompose,
					composer_factory=self.__composer_factory
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
