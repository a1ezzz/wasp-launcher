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
from wasp_general.command.command import WCommandResult, WCommand
from wasp_general.command.context import WCommandContext, WContextProto, WCommandContextAdapter

from wasp_general.cli.cli import WConsoleBase
from wasp_general.cli.curses import WCursesConsole
from wasp_general.cli.curses_commands import WExitCommand, WEmptyCommand

from wasp_general.task.thread import WThreadTask

from wasp_general.network.messenger.proto import WMessengerOnionSessionFlowProto, WMessengerOnionLayerProto
from wasp_general.network.messenger.proto import WMessengerEnvelopeProto, WMessengerOnionSessionProto
from wasp_general.network.messenger.onion import WMessengerOnion
from wasp_general.network.messenger.layers import WMessengerOnionCoderLayerProto, WMessengerOnionPackerLayerProto
from wasp_general.network.messenger.envelope import WMessengerEnvelope
from wasp_general.network.messenger.session import WMessengerOnionSessionFlow, WMessengerOnionSession

from wasp_launcher.host_apps.broker import WBrokerClientTask, WManagementCommandPackerLayer
from wasp_launcher.host_apps.broker import WManagementResultPackerLayer
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

	def broker(self):
		return self.__broker

	def start(self):
		self.__broker.start()
		WCursesConsole.start(self)

	def stop(self):
		self.__broker.stop()
		WCursesConsole.stop(self)

	def prompt(self):
		return self.command_set().context_prompt() + '> '


class WBrokerCommandProxy(WCommandContext):

	class ConsoleOutputLayer(WMessengerOnionLayerProto):

		__layer_name__ = "com.binblob.wasp-launcher.console-output-layer"
		""" Layer name
		"""

		@verify_type(console=WConsoleBase)
		def __init__(self, console):
			WMessengerOnionLayerProto.__init__(self, WBrokerCommandProxy.ConsoleOutputLayer.__layer_name__)
			self.__console = console
			self.__last_feedback_length = None

		def console(self):
			return self.__console

		def undo_feedback(self):
			if self.__last_feedback_length is not None:
				self.console().truncate(self.__last_feedback_length)
				self.__last_feedback_length = None

		@verify_type(envelope=WMessengerEnvelopeProto, session=WMessengerOnionSessionProto)
		@verify_type(feedback=(str, None), undo_previous=(bool, None), cr=(bool, None))
		@verify_type(refresh_window=(bool, None))
		def process(
			self, envelope, session, feedback=None, undo_previous=None, cr=None, refresh_window=None,
			**kwargs
		):
			if undo_previous is not None and undo_previous is True:
				self.undo_feedback()
			if feedback is not None:
				self.__last_feedback_length = len(feedback)
				cr = cr if cr is not None else True
				if cr is True:
					self.__last_feedback_length += 1
				self.console().write(feedback, cr=cr)
			if refresh_window is not None and refresh_window is True:
				self.console().refresh_window()
			return envelope


	@verify_type(console=WBrokerCLI)
	def __init__(self, console):

		class DummyCommand(WCommand):
			def _exec(self, *command_tokens):
				pass

		class DummyAdapter(WCommandContextAdapter):
			def adapt(self, *command_tokens, request_context=None):
				pass

		WCommandContext.__init__(self, DummyCommand(), DummyAdapter(None))
		self.__console = console
		self.__command_timeout = WAppsGlobals.config.getint(
			'wasp-launcher::broker::connection::cli', 'command_timeout'
		)

		self.__onion = WMessengerOnion()
		self.__console_output_layer = WBrokerCommandProxy.ConsoleOutputLayer(self.__console)
		self.__onion.add_layers(
			self.__console_output_layer, WManagementCommandPackerLayer(), WManagementResultPackerLayer()
		)

	@verify_type(command_tokens=str)
	def match(self, *command_tokens):
		return len(command_tokens) > 0

	@verify_type(command_tokens=str, request_context=(WContextProto, None))
	def match_context(self, *command_tokens, request_context=None):
		return len(command_tokens) > 0

	@verify_type(command_tokens=str, request_context=(WContextProto, None))
	def exec_context(self, *command_tokens, request_context=None):
		broker = self.__console.broker()
		handler = broker.handler()
		receive_agent = broker.receive_agent()
		send_agent = broker.send_agent()

		session_flow = WMessengerOnionSessionFlow.sequence_flow(
			WMessengerOnionSessionFlowProto.IteratorInfo(
				'com.binblob.wasp-launcher.broker-management-command-packer',
				mode=WMessengerOnionPackerLayerProto.Mode.pack,
				command=WManagementCommandPackerLayer.Command.create(
					*command_tokens, request_context=request_context
				)
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
				'com.binblob.wasp-launcher.console-output-layer',
				feedback='Command is sending', refresh_window=True
			),
			WMessengerOnionSessionFlowProto.IteratorInfo(
				'com.binblob.wasp-general.send-agent-layer',
				send_agent=send_agent, handler=handler
			),
			WMessengerOnionSessionFlowProto.IteratorInfo(
				'com.binblob.wasp-launcher.console-output-layer',
				feedback='Response is awaiting', undo_previous=True, refresh_window=True
			),
			WMessengerOnionSessionFlowProto.IteratorInfo(
				'com.binblob.wasp-general.sync-receive-agent-layer',
				receive_agent=receive_agent
			),
			WMessengerOnionSessionFlowProto.IteratorInfo(
				'com.binblob.wasp-launcher.console-output-layer',
				undo_previous=True, refresh_window=True
			),
			WMessengerOnionSessionFlowProto.IteratorInfo(
				'com.binblob.wasp-general.encoding-layer',
				mode=WMessengerOnionCoderLayerProto.Mode.decode
			),
			WMessengerOnionSessionFlowProto.IteratorInfo(
				'com.binblob.wasp-general.json-packer-layer',
				mode=WMessengerOnionPackerLayerProto.Mode.unpack
			),
			WMessengerOnionSessionFlowProto.IteratorInfo(
				'com.binblob.wasp-launcher.broker-management-result-packer',
				mode=WMessengerOnionPackerLayerProto.Mode.unpack
			)
		)

		session = WMessengerOnionSession(self.__onion, session_flow)
		try:
			envelope = session.process(WMessengerEnvelope(None))
			return envelope.message()
		except TimeoutError:
			self.__console_output_layer.undo_feedback()
			return WCommandResult(error='Command completion timeout expired')
