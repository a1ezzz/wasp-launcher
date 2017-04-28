# -*- coding: utf-8 -*-
# wasp_launcher/host_apps/guest_apps.py
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

from importlib import import_module

from wasp_launcher.apps import WSyncHostApp, WGuestApp, WAppsGlobals


class WGuestAppLoader(WSyncHostApp):

	__registry_tag__ = 'com.binblob.wasp-launcher.host-app.guest-apps::load'
	__dependency__ = [
		'com.binblob.wasp-launcher.host-app.config'
	]

	__module_export_function__ = '__wasp_launcher_apps__'

	def start(self):
		WAppsGlobals.apps_registry.clear()
		self.load_applications()

	def stop(self):
		WAppsGlobals.apps_registry.clear()

	@classmethod
	def load_applications(cls):
		WAppsGlobals.log.info('Reading modules for available local applications')

		module_names = WAppsGlobals.config.split_option(
			'wasp-launcher::applications', 'applications_modules'
		)
		apps_count = 0
		for name in module_names:
			try:
				module = import_module(name)
				if hasattr(module, cls.__module_export_function__):
					export_fn = getattr(module, cls.__module_export_function__)
					for app in export_fn():
						if issubclass(app, WGuestApp) is True:
							WAppsGlobals.apps_registry.add(app)
							apps_count += 1
						else:
							raise TypeError(
								'Invalid application type: %s' % str(type(app))
							)

			except Exception as e:
				WAppsGlobals.log.error(
					'Unable to load "%s" module. Exception was thrown: %s' % (name, str(e))
				)
		WAppsGlobals.log.info('Available local applications: %i' % apps_count)


class WGuestAppStarter(WSyncHostApp):

	__registry_tag__ = 'com.binblob.wasp-launcher.host-app.guest-apps::start'

	__dependency__ = [
		'com.binblob.wasp-launcher.host-app.model-load',
		'com.binblob.wasp-launcher.host-app.web::init'
	]

	def __init__(self):
		WSyncHostApp.__init__(self)
		self.__loaded_apps = []

	def start(self):
		self.__loaded_apps.clear()
		self.start_apps()

	def stop(self):
		for app_name in self.__loaded_apps:
			WAppsGlobals.log.info('Stopping "%s" application and its dependencies' % app_name)
			WAppsGlobals.apps_registry.stop_task(app_name)
		self.__loaded_apps.clear()

	def start_apps(self):

		enabled_applications = WAppsGlobals.config.split_option(
			'wasp-launcher::applications', 'load_applications'
		)

		WAppsGlobals.log.info('Starting enabled local applications (total: %i)' % len(enabled_applications))

		for app_name in enabled_applications:
			app = WAppsGlobals.apps_registry.registry_storage().tasks(app_name)
			if app is None:
				raise RuntimeError('Application "%s" was not found' % app_name)
			WAppsGlobals.log.info('Starting "%s" application and its dependencies' % app_name)
			WAppsGlobals.apps_registry.start_task(app_name)
			self.__loaded_apps.append(app_name)
			WAppsGlobals.log.info('Application "%s" started' % app_name)
