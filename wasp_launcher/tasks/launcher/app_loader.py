# -*- coding: utf-8 -*-
# wasp_launcher/tasks/launcher/tasks/launcher/app_loader.py
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

from wasp_launcher.tasks.launcher.registry import WLauncherTask
from wasp_launcher.tasks.launcher.globals import WLauncherGlobals
from wasp_launcher.app import WLauncherAppDescriptor

from importlib import import_module


class WLauncherAppLoader(WLauncherTask):

	__registry_tag__ = 'com.binblob.wasp-launcher.launcher.app_loader::load'
	__dependency__ = [
		'com.binblob.wasp-launcher.launcher.log::log_setup',
		'com.binblob.wasp-launcher.launcher.config::read_config'
	]

	__module_export_function__ = '__wasp_launcher_apps__'

	def start(self):
		WLauncherGlobals.apps_registry.clear()
		self.load_applications()

	def stop(self):
		WLauncherGlobals.apps_registry.clear()

	@classmethod
	def load_applications(cls):
		WLauncherGlobals.log.info('Reading modules for available local applications')

		module_names = WLauncherGlobals.config.split_option(
			'wasp-launcher::applications', 'applications_modules'
		)
		apps_count = 0
		for name in module_names:
			try:
				module = import_module(name)
				if hasattr(module, cls.__module_export_function__):
					export_fn = getattr(module, cls.__module_export_function__)
					for app in export_fn():
						if isinstance(app, WLauncherAppDescriptor) is True:
							WLauncherGlobals.apps_registry.add(app)
							apps_count += 1
						else:
							raise TypeError(
								'Invalid application type: %s' % str(type(app))
							)

			except Exception as e:
				WLauncherGlobals.log.error(
					'Unable to load "%s" module. Exception was thrown: %s' % (name, str(e))
				)
		WLauncherGlobals.log.info('Available local applications: %i' % apps_count)
