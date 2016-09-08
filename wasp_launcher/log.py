# -*- coding: utf-8 -*-
# wasp_launcher/log.py
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

# noinspection PyUnresolvedReferences
from wasp_launcher.version import __author__, __version__, __credits__, __license__, __copyright__, __email__
# noinspection PyUnresolvedReferences
from wasp_launcher.version import __status__

import logging
import logging.config
import sys

from wasp_launcher.launcher_registry import WLauncherTask
from wasp_launcher.globals import WLauncherGlobals


class WLauncherLogSetup(WLauncherTask):
	""" Task that initialized logger
	"""
	__registry_tag__ = '::wasp_launcher::log::log_setup'
	""" Task tag
	"""

	def start(self):
		""" Start this task (all the work is done in :meth:`.WLauncherLogSetup.setup_logger` method)

		:return: None
		"""
		self.setup_logger()
		WLauncherGlobals.log.info('Logger initialised')

	def stop(self):
		""" "Uninitialize" logger. Makes :attr:`wasp_launcher.globals.WLauncherGlobals.log` logger unavailable

		:return: None
		"""
		WLauncherGlobals.log = None

	@classmethod
	def setup_logger(cls):
		""" Initialize :attr:`wasp_launcher.globals.WLauncherGlobals.log` log.

		:return: None
		"""
		if WLauncherGlobals.log is None:
			WLauncherGlobals.log = logging.getLogger("wasp-launcher")
			formatter = logging.Formatter(
				'[%(name)s] [%(threadName)s] [%(levelname)s] [%(asctime)s] %(message)s',
				'%Y-%m-%d %H:%M:%S'
			)
			log_handler = logging.StreamHandler(sys.stdout)
			log_handler.setFormatter(formatter)
			WLauncherGlobals.log.addHandler(log_handler)
			WLauncherGlobals.log.setLevel(logging.INFO)
