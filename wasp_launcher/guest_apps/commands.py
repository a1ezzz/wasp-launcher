# -*- coding: utf-8 -*-
# wasp_launcher/guest_apps/commands.py
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

from wasp_launcher.apps import WBrokerCommands

from wasp_general.command.command import WCommand, WCommandResult


class WSystemCommands:

	class Threads(WCommand):

		def __init__(self):
			WCommand.__init__(self, 'system', 'threads')

		def _exec(self, *command_tokens):
			threads = threading.enumerate()
			output = 'Total threads: %i' % len(threads)
			if len(threads) > 0:
				output += '\n\tThread name\n\t==========='
				for thread in threads:
					output += '\n\t' + thread.name

			return WCommandResult(output=output)


class WWaspBrokerCommands(WBrokerCommands):

	__registry_tag__ = 'com.binblob.wasp-launcher.guest-apps.broker-commands'

	@classmethod
	def commands(cls):
		return [WSystemCommands.Threads()]
