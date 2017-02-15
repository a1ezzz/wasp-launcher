# -*- coding: utf-8 -*-
# wasp_launcher/tasks/launcher/apps.py
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

from wasp_general.task.thread import WThreadTask
from wasp_general.task.dependency import WDependentTask

from wasp_launcher.tasks.launcher.registry import WLauncherTask
from wasp_launcher.tasks.launcher.globals import WLauncherGlobals


class WLauncherAppDescriptor(WThreadTask, metaclass=WDependentTask):

	__auto_registry__ = False

	@classmethod
	def name(cls):
		return cls.__registry_tag__

	@classmethod
	def description(cls):
		return None


class WLauncherWebAppDescriptor(WLauncherAppDescriptor):

	@classmethod
	def public_presenters(cls):
		return tuple()

	@classmethod
	def public_routes(cls):
		""" Return routes which are published by an application

		:return: tuple of WWebRoute
		"""
		return tuple()

	@classmethod
	def template_path(cls):
		'''

		can be none or non-existens path

		:return:
		'''
		return None

	@classmethod
	def py_templates_package(cls):
		return None

	@classmethod
	def static_files_path(cls):
		'''

		can be none or non-existens path

		:return:
		'''
		return None

	def start(self):
		for presenter in self.public_presenters():
			WLauncherGlobals.wasp_web_service.add_presenter(presenter)
			WLauncherGlobals.log.info(
				'Presenter "%s" was added to the web service registry' % presenter.__presenter_name__()
			)
		for route in self.public_routes():
			WLauncherGlobals.wasp_web_service.route_map().append(route)

	def stop(self):
		pass


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
						if issubclass(app, WLauncherAppDescriptor) is True:
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


class WLauncherAppStarter(WLauncherTask):

	__registry_tag__ = 'com.binblob.wasp-launcher.launcher.app_starter::start'

	__dependency__ = [
		'com.binblob.wasp-launcher.launcher.log::log_setup',
		'com.binblob.wasp-launcher.launcher.config::read_config',
		'com.binblob.wasp-launcher.launcher.app_loader::load',
		'com.binblob.wasp-launcher.launcher.web_service::pre_init'
	]

	def __init__(self):
		WLauncherTask.__init__(self)
		self.__loaded_apps = []

	def start(self):
		self.__loaded_apps.clear()
		self.start_apps()

	def stop(self):
		for app_name in self.__loaded_apps:
			WLauncherGlobals.log.info('Stopping "%s" application and its dependencies' % app_name)
			WLauncherGlobals.apps_registry.stop_task(app_name)
		self.__loaded_apps.clear()

	def start_apps(self):

		enabled_applications = WLauncherGlobals.config.split_option(
			'wasp-launcher::applications', 'load_applications'
		)

		WLauncherGlobals.log.info('Starting enabled local applications (total: %i)' % len(enabled_applications))

		for app_name in enabled_applications:
			app = WLauncherGlobals.apps_registry.registry_storage().tasks(app_name)
			if app is None:
				raise RuntimeError('Application "%s" was not found' % app_name)
			WLauncherGlobals.log.info('Starting "%s" application and its dependencies' % app_name)
			WLauncherGlobals.apps_registry.start_task(app_name)
			self.__loaded_apps.append(app_name)
			WLauncherGlobals.log.info('Application "%s" started' % app_name)
