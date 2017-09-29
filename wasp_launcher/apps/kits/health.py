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
from wasp_general.cli.formatter import WConsoleTableFormatter
from wasp_general.command.command import WCommandResult

from wasp_launcher.core import WCommandKit, WBrokerCommand


class WHealthCommandKit(WCommandKit):

	__registry_tag__ = 'com.binblob.wasp-launcher.broker.kits.health'

	class Threads(WBrokerCommand):

		def __init__(self):
			WBrokerCommand.__init__(self, 'threads')

		@verify_type(command_arguments=dict)
		def _exec(self, command_arguments):
			threads = threading.enumerate()

			table_formatter = WConsoleTableFormatter('Thread name')
			for thread in threads:
				table_formatter.add_row(thread.name)

			header = 'Total threads: %i\n' % len(threads)
			return WCommandResult(output=header + table_formatter.format())

		@classmethod
		def brief_description(cls):
			return 'return application threads list'

	@classmethod
	def description(cls):
		return 'general or launcher-wide commands'

	@classmethod
	def commands(cls):
		return [WHealthCommandKit.Threads()]
