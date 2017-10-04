# -*- coding: utf-8 -*-
# wasp_launcher/mongodb.py
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

import time
from pymongo import MongoClient

from wasp_general.verify import verify_type, verify_value

from wasp_launcher.core import WAppsGlobals


class WMongoConnection:

	@verify_type(connection=str, database_name=str, rude_closing=bool)
	@verify_value(connection=lambda x: len(x) > 0, database_name=lambda x: len(x) > 0)
	def __init__(self, connection, database_name, rude_closing=False):
		self.__connection = connection
		self.__client = MongoClient(connection)
		self.__database_name = database_name
		self.__database = self.__client[self.__database_name]
		self.__rude_closing = rude_closing

	def connection(self):
		return self.__connection

	def client(self):
		return self.__client

	def database_name(self):
		return self.__database_name

	def database(self):
		return self.__database

	def close(self):
		self.__client.close()
		if self.__rude_closing is True:  # pymongo doesn't terminate some threads - stop them manually
			self.__client._topology.close()  # terminate "pymongo_server_monitor_thread" thread
			self.__client._kill_cursors_executor.close()  # terminate "pymongo_kill_cursors_thread" thread
			self.__client._kill_cursors_executor.join()  # wait for pymongo_kill_cursors_thread termination
			time.sleep(0.5) # we have to wait for "pymongo_server_monitor_thread" this dirty way
			# because there is now join function

	@verify_type(item=str)
	@verify_value(item=lambda x: len(x) > 0)
	def __getitem__(self, item):
		return self.database()[item]

	@staticmethod
	@verify_type(config_section=str, connection_option=str, database_option=str, rude_closing=bool)
	def create(config_section, connection_option, database_option, rude_closing=False):
		return WMongoConnection(
			WAppsGlobals.config[config_section][connection_option],
			WAppsGlobals.config[config_section][database_option],
			rude_closing=rude_closing
		)
