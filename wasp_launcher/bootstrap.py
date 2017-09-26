# -*- coding: utf-8 -*-
# wasp_launcher/bootstrap.py
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

from wasp_general.task.dependency import WTaskDependencyRegistry, WTaskDependencyRegistryStorage

from wasp_launcher.apps import WAppsGlobals, WHostAppRegistry, WRegisteredHostApp
from wasp_launcher.host_apps.log import WLogHostApp
from wasp_launcher.host_apps.config import WConfigHostApp
from wasp_launcher.loader import WClassLoader


class WBootstrapRegistry(WTaskDependencyRegistry):
	__registry_storage__ = WTaskDependencyRegistryStorage()


class WBootstrapLog(WLogHostApp):
	__registry__ = WBootstrapRegistry
	__auto_registry__ = True


class WBootstrapConfig(WConfigHostApp):
	__registry__ = WBootstrapRegistry
	__auto_registry__ = True


class WLauncherBootstrap:

	__host_app_section_prefix__ = 'wasp-launcher::applications::host'

	def __init__(self):
		self.__start_apps = []
		self.__loader = WClassLoader(
			self.__host_app_section_prefix__, WRegisteredHostApp, tag_fn=lambda x: x.__registry_tag__
		)

	def load_configuration(self):
		WBootstrapRegistry.start_task(WBootstrapConfig.__registry_tag__)

		def load_callback(section_name, item_tag, item_cls):
			WHostAppRegistry.add(item_cls)
			if WAppsGlobals.config.getboolean(section_name, 'auto_start') is True:
				self.__start_apps.append(item_tag)

		self.__loader.load(load_callback)

	def stop_bootstrapping(self):
		WBootstrapRegistry.all_stop()

	def start_apps(self):
		for task_tag in self.__start_apps:
			WHostAppRegistry.start_task(task_tag)