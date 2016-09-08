# -*- coding: utf-8 -*-
# wasp_launcher/<FILENAME>.py
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

import os

from wasp_general.config import WConfig

from wasp_launcher.launcher_registry import WLauncherTask
from wasp_launcher.globals import WLauncherGlobals


class WLauncherConfig(WLauncherTask):
	""" Task that load configuration
	"""

	__registry_tag__ = '::wasp_launcher::config::read_config'
	""" Task tag
	"""

	__dependency__ = ['::wasp_launcher::log::log_setup']
	""" Task dependency
	"""

	__environment_var__ = 'WASP_LAUNCHER_CONFIG_FILE'
	""" Environment variable name that is used for configuration filename which overrides defaults.
	"""

	__configuration_default__ = os.path.join(os.path.dirname(__file__), 'config', 'defaults.ini')
	""" Place where default configuration is stored
	"""

	def start(self):
		""" Start this task (all the work is done in :meth:`.WLauncherConfig.read_config` method)

		:return: None
		"""
		self.read_config()
		WLauncherGlobals.log.info('Configuration loading finished')

	def stop(self):
		""" Remove configuration from application.
		Makes :attr:`wasp_launcher.globals.WLauncherGlobals.config` configuration unavailable

		:return: None
		"""
		WLauncherGlobals.config = None

	@classmethod
	def read_config(cls):
		""" Setup :attr:`wasp_launcher.globals.WLauncherGlobals.log` configuration. Reads defaults and
		override it by a file given via :attr:`WLauncherConfig.__environment_var__` environment variable

		:return: None
		"""
		WLauncherGlobals.config = WConfig()

		def load(filename):
			if os.path.isfile(filename) is False:
				raise RuntimeError("Invalid configuration: '%s'" % filename)
			WLauncherGlobals.config.merge(filename)
			WLauncherGlobals.log.info('Configuration loaded from file: %s' % filename)

		load(cls.__configuration_default__)

		if cls.__environment_var__ in os.environ:
			WLauncherGlobals.log.info('Variable %s was set' % cls.__environment_var__)
			load(os.environ[cls.__environment_var__])