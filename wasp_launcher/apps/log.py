# -*- coding: utf-8 -*-
# wasp_launcher/apps/log.py
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

# noinspection PyUnresolvedReferences
from wasp_launcher.version import __author__, __version__, __credits__, __license__, __copyright__, __email__
# noinspection PyUnresolvedReferences
from wasp_launcher.version import __status__

import logging
import logging.config
import sys

from wasp_launcher.core import WSyncApp, WAppsGlobals


class WLogApp(WSyncApp):
	""" Logger application
	"""

	__registry_tag__ = 'com.binblob.wasp-launcher.app.log'
	""" Task tag
	"""

	__log_handler__ = None
	""" Logging handler that is used for processing messages
	"""

	def start(self):
		""" Start this app (all the work is done in :meth:`.WLogApp.setup_logger` method)

		:return: None
		"""
		self.setup_logger()
		WAppsGlobals.log.info('Logger initialised')

	def stop(self):
		""" "Uninitialize" logger. Makes :attr:`wasp_launcher.apps.WAppsGlobals.log` logger unavailable

		:return: None
		"""
		if WAppsGlobals.log is not None and WLogApp.__log_handler__ is not None:
			WAppsGlobals.log.removeHandler(WLogApp.__log_handler__)

		WLogApp.__log_handler__ = None
		WAppsGlobals.log = None

	@classmethod
	def setup_logger(cls):
		""" Initialize :attr:`wasp_launcher.apps.WAppsGlobals.log` log.

		:return: None
		"""
		if WAppsGlobals.log is None:
			WAppsGlobals.log = logging.getLogger("wasp-launcher")
			formatter = logging.Formatter(
				'[%(name)s] [%(threadName)s] [%(levelname)s] [%(asctime)s] %(message)s',
				'%Y-%m-%d %H:%M:%S'
			)
			WLogApp.__log_handler__ = logging.StreamHandler(sys.stdout)
			WLogApp.__log_handler__.setFormatter(formatter)
			WAppsGlobals.log.addHandler(WLogApp.__log_handler__)
			WAppsGlobals.log.setLevel(logging.INFO)
