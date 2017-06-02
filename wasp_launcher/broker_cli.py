# -*- coding: utf-8 -*-
# wasp_launcher/broker_cli.py
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

from wasp_general.verify import verify_type

from wasp_general.command.context import WCommandContextSet
from wasp_general.command.command import WCommandProto, WCommandResult

from wasp_general.cli.curses import WCursesConsole
from wasp_general.cli.curses_commands import WExitCommand, WEmptyCommand

from wasp_general.task.thread import WThreadTask

from wasp_general.network.messenger.proto import WMessengerOnionSessionFlowProto, WMessengerOnionLayerProto
from wasp_general.network.messenger.onion import WMessengerOnion
from wasp_general.network.messenger.layers import WMessengerOnionCoderLayerProto, WMessengerOnionPackerLayerProto
from wasp_general.network.messenger.envelope import WMessengerEnvelope, WMessengerBytesEnvelope
from wasp_general.network.messenger.session import WMessengerOnionSessionFlow, WMessengerOnionSession
from wasp_general.network.messenger.coders import WMessengerEncodingLayer
from wasp_general.network.messenger.packers import WMessengerJSONPacker

from wasp_launcher.host_apps.broker import WBrokerClientTask
from wasp_launcher.apps import WAppsGlobals


class WBrokerClientCommandSet(WCommandContextSet):

	@verify_type(console=WCursesConsole)
	def __init__(self, console):
		WCommandContextSet.__init__(self)
		self.commands().add(WExitCommand(console))
		self.commands().add(WEmptyCommand())
		self.commands().add_prioritized(WBrokerCommandProxy(console), 40)

	def context_prompt(self):
		context = self.context()
		if context is None:
			return ''

		names = [x.context_name() for x in context]
		names.reverse()
		return '[%s] ' % '::'.join(names)


class WBrokerCLI(WCursesConsole, WThreadTask):

	__thread_name__ = 'Broker-CLI'

	@verify_type(connction=str)
	def __init__(self, connection):
		WCursesConsole.__init__(self, WBrokerClientCommandSet(self))
		WThreadTask.__init__(self)
		self.__broker = WBrokerClientTask(connection)

	def receive_agent(self):
		return self.__broker.receive_agent()

	def start(self):
		self.__broker.start()
		WCursesConsole.start(self)

	def stop(self):
		self.__broker.stop()
		WCursesConsole.stop(self)

	def prompt(self):
		return self.command_set().context_prompt() + '> '


class WBrokerCommandProxy(WCommandProto):

	class ConsoleOutputLayer(WMessengerOnionLayerProto):
		pass

	@verify_type(console=WBrokerCLI)
	def __init__(self, console):
		WCommandProto.__init__(self)
		self.__console = console
		self.__command_timeout = WAppsGlobals.config.getint(
			'wasp-launcher::broker::connection::cli', 'command_timeout'
		)

		self.__onion = WMessengerOnion()
		self.__outbound_session_flow = WMessengerOnionSessionFlow.sequence_flow(
			WMessengerOnionSessionFlowProto.IteratorInfo(
				'com.binblob.wasp-general.json-packer-layer',
				mode=WMessengerOnionPackerLayerProto.Mode.pack
			),
			WMessengerOnionSessionFlowProto.IteratorInfo(
				'com.binblob.wasp-general.encoding-layer',
				mode=WMessengerOnionCoderLayerProto.Mode.encode
			)
		)

		self.__inbound_session_flow = WMessengerOnionSessionFlow.sequence_flow(
			WMessengerOnionSessionFlowProto.IteratorInfo(
				'com.binblob.wasp-general.encoding-layer',
				mode=WMessengerOnionCoderLayerProto.Mode.decode
			),
			WMessengerOnionSessionFlowProto.IteratorInfo(
				'com.binblob.wasp-general.json-packer-layer',
				mode=WMessengerOnionPackerLayerProto.Mode.unpack
			)
		)

	@verify_type(command_tokens=str)
	def match(self, *command_tokens):
		return len(command_tokens) > 0

	@verify_type(command_tokens=str)
	def exec(self, *command_tokens):

		receive_agent = self.__console.receive_agent()
		outbound_session = WMessengerOnionSession(self.__onion, self.__outbound_session_flow)
		inbound_session = WMessengerOnionSession(self.__onion, self.__inbound_session_flow)

		def request():
			sending_command_message = 'Command is sending'
			self.__console.write(sending_command_message)
			self.__console.refresh_window()

			envelope = outbound_session.process(WMessengerEnvelope(command_tokens))
			receive_agent.send(envelope.message())

			self.__console.truncate(len(sending_command_message) + 1)
			response_awaiting_message = 'Response awaiting'
			self.__console.write(response_awaiting_message)
			self.__console.refresh_window()

			status = receive_agent.event().wait(receive_agent.timeout())
			self.__console.truncate(len(response_awaiting_message) + 1)
			if status is True:
				envelope = inbound_session.process(
					WMessengerBytesEnvelope(b''.join(receive_agent.data())))
				return WCommandResult(output=str(envelope.message()))
			else:
				return WCommandResult(error='Command completion timeout expired')

		return request()
