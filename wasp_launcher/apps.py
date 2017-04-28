# -*- coding: utf-8 -*-
# wasp_launcher/guest_apps.py
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
# TODO: test the code

# noinspection PyUnresolvedReferences
from wasp_launcher.version import __author__, __version__, __credits__, __license__, __copyright__, __email__
# noinspection PyUnresolvedReferences
from wasp_launcher.version import __status__

from wasp_general.task.dependency import WTaskDependencyRegistry, WTaskDependencyRegistryStorage, WDependentTask
from wasp_general.task.base import WTask
from wasp_general.task.sync import WSyncTask
from wasp_general.task.thread import WThreadTask


from wasp_general.task.dependency import WTaskDependencyRegistry, WTaskDependencyRegistryStorage


class WHostAppRegistry(WTaskDependencyRegistry):
	""" Main registry to keep host applications
	"""
	__registry_storage__ = WTaskDependencyRegistryStorage()
	""" Default storage for this type of registry
	"""


class WRegisteredHostApp(WTask, metaclass=WDependentTask):
	""" Base class for registered host apps, such application maintains core functionality and creates environment
	for guest application to work. This class defines link to the registry, which holds every host app.
	"""

	__registry__ = WHostAppRegistry
	""" Link to registry
	"""


class WSyncHostApp(WRegisteredHostApp, WSyncTask, metaclass=WDependentTask):
	""" Host application, that executes in foreground
	"""
	pass


class WThreadedHostApp(WRegisteredHostApp, WThreadTask, metaclass=WDependentTask):
	""" Host application, that executes in a separate thread
	"""
	pass


class WGuestAppRegistry(WTaskDependencyRegistry):
	__registry_storage__ = WTaskDependencyRegistryStorage()


class WGuestApp(WSyncTask, metaclass=WDependentTask):

	__auto_registry__ = False

	@classmethod
	def name(cls):
		return cls.__registry_tag__

	@classmethod
	def description(cls):
		return None


class WGuestWebApp(WGuestApp):

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
			WAppsGlobals.wasp_web_service.add_presenter(presenter)
			WAppsGlobals.log.info(
				'Presenter "%s" was added to the web service registry' % presenter.__presenter_name__()
			)
		for route in self.public_routes():
			WAppsGlobals.wasp_web_service.route_map().append(route)

	def stop(self):
		pass


class WGuestModelApp(WGuestApp):

	def start(self):
		pass

	def stop(self):
		pass


class WAppsGlobals:
	""" Storage of global variables, that are widely used across all application
	"""

	log = None
	""" Application logger (logging.Logger instance. See :class:`wasp_launcher.host_apps.log.WLauncherLogSetupApp`)
	"""

	config = None
	""" Current server configuration (wasp_general.config.WConfig instance.
	See :class:`wasp_launcher.host_apps.config.WLauncherConfigApp`)
	"""

	apps_registry = WGuestAppRegistry
	templates = None

	models = None

	wasp_web_service = None
	tornado_io_loop = None
	tornado_service = None
