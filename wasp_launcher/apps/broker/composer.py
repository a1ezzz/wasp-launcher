# -*- coding: utf-8 -*-
# wasp_launcher/apps/broker/composer.py
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

from wasp_general.composer import WComposerFactory, WClassComposer, WIterComposer, WPlainComposer, WDictComposer
from wasp_general.command.result import WPlainCommandResult, WExceptionResult

from wasp_general.command.context import WContextComposer


class WCommandRequest:

	def __init__(self, *command_tokens, **command_env):
		self.command_tokens = command_tokens
		self.command_env = command_env


class WLauncherComposerFactory(WComposerFactory):

	__env_composer__ = WDictComposer(
		WDictComposer.DictKey('command_context', WContextComposer()),
		WDictComposer.DictKey('broker_last_task', WPlainComposer(strict_cls=str, permit_none=True)),
		WDictComposer.DictKey('broker_selected_task', WPlainComposer(strict_cls=str, permit_none=True))
	)

	__str_key__ = WClassComposer.GetterKey('__str__', WPlainComposer(strict_cls=str), required=True)
	__env_key__ = WClassComposer.GetterKey('environment', __env_composer__, required=False)

	def __init__(self):

		command_request_composer = WClassComposer(
			WClassComposer.ClassKey(
				'command_tokens', WIterComposer(WPlainComposer(strict_cls=str)), required=True
			),
			WClassComposer.ClassKey(
				'command_env', WLauncherComposerFactory.__env_composer__, required=True
			),
			constructor=WClassComposer.ClassConstructor(WCommandRequest)
		)

		plain_result_composer = WClassComposer(
			WLauncherComposerFactory.__str_key__,
			WLauncherComposerFactory.__env_key__,
			constructor=WClassComposer.ClassConstructor(
				WPlainCommandResult, create_obj_fn=self.create_plain_result
			)
		)

		exception_result_composer = WClassComposer(
			WClassComposer.ClassKey(
				'message',
				WPlainComposer(strict_cls=str),
				has_key_fn=lambda o, k: True,
				get_key_fn=lambda o, k: o.message(),
				set_key_fn=lambda o, k, v: None,
				required=True
			),
			WClassComposer.ClassKey(
				'exception',
				WPlainComposer(strict_cls=str),
				has_key_fn=lambda o, k: True,
				get_key_fn=lambda o, k: o.exception(),
				set_key_fn=lambda o, k, v: None,
				required=True
			),
			WClassComposer.ClassKey(
				'traceback',
				WPlainComposer(strict_cls=str),
				has_key_fn=lambda o, k: True,
				get_key_fn=lambda o, k: o.traceback(),
				set_key_fn=lambda o, k, v: None,
				required=True
			),
			WLauncherComposerFactory.__env_key__,
			constructor=WClassComposer.ClassConstructor(
				WExceptionResult, create_obj_fn=self.create_exception_result
			)
		)

		WComposerFactory.__init__(
			self,
			WComposerFactory.Entry(command_request_composer),
			WComposerFactory.Entry(plain_result_composer),
			WComposerFactory.Entry(exception_result_composer)
		)

	@staticmethod
	def create_plain_result(construction_keys):
		str_value = construction_keys['__str__'].value
		environment_pair = construction_keys['environment'].value
		return WPlainCommandResult(str_value, **environment_pair)

	@staticmethod
	def create_exception_result(construction_keys):
		message = construction_keys['message'].value
		exc = construction_keys['exception'].value
		traceback = construction_keys['traceback'].value
		environment_pair = construction_keys['environment'].value
		return WExceptionResult(message, exc, traceback, **environment_pair)
