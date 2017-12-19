# -*- coding: utf-8 -*-
# wasp_launcher/apps/kits/health.py
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

import threading

from wasp_general.verify import verify_type

from wasp_launcher.core_broker import WCommandKit, WTemplateBrokerCommand


class WHealthCommandKit(WCommandKit):

	__registry_tag__ = 'com.binblob.wasp-launcher.broker.kits.health'

	class ThreadsCommand(WTemplateBrokerCommand):

		def __init__(self):
			WTemplateBrokerCommand.__init__(
				self,
				'mako::com.binblob.wasp-launcher.broker::health::threads.mako',
				'threads',
				template_context={}
			)

		@verify_type(broker_last_task=(str, None), broker_selected_task=(str, None))
		def result_template(
			self, *command_tokens, broker_last_task=None, broker_selected_task=None, **command_env
		):
			result = WTemplateBrokerCommand.result_template(self, *command_tokens, **command_env)
			result.update_context(threads=[x.name for x in threading.enumerate()])
			return result

		def brief_description(self):
			return ''

	@classmethod
	def description(cls):
		return 'shows launcher and application "health" information'

	@classmethod
	def commands(cls):
		return [WHealthCommandKit.ThreadsCommand()]
