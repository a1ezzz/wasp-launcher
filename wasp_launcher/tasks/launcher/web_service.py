# -*- coding: utf-8 -*-
# wasp_launcher/tasks/launcher/web_service.py
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

import tornado.ioloop
import tornado.web
import tornado.httpserver

from wasp_network.web.service import WWebService
from wasp_network.web.tornado import WTornadoRequestHandler

from wasp_launcher.tasks.launcher.registry import WLauncherTask
from wasp_launcher.tasks.launcher.globals import WLauncherGlobals
from wasp_launcher.tasks.launcher.web_debugger import WLauncherWebDebugger
from wasp_launcher.app import WLauncherWebAppDescriptor


class WLauncherWebServicePreInit(WLauncherTask):
	""" Task that prepare web-service
	"""

	__registry_tag__ = 'com.binblob.wasp-launcher.launcher.web_service::pre_init'
	""" Task tag
	"""

	__dependency__ = [
		'com.binblob.wasp-launcher.launcher.log::log_setup',
		'com.binblob.wasp-launcher.launcher.config::read_config',
		'com.binblob.wasp-launcher.launcher.app_loader::load'
	]
	""" Task dependency
	"""

	def start(self):
		WLauncherGlobals.wasp_web_service = WWebService(debugger=WLauncherWebDebugger())
		WLauncherGlobals.tornado_io_loop = tornado.ioloop.IOLoop()
		WLauncherGlobals.tornado_service = tornado.httpserver.HTTPServer(
			tornado.web.Application([
				(r".*", WTornadoRequestHandler.__handler__(WLauncherGlobals.wasp_web_service))
			]), io_loop=WLauncherGlobals.tornado_io_loop
		)

		WLauncherGlobals.log.info('Web-service is ready to start (initialized)')

		if WLauncherGlobals.config["wasp-launcher::web:debug"]["mode"].lower() in ['on', 'on error']:
			self.__registry__.start_task('com.binblob.wasp-launcher.launcher.web_debugger::connection')

	def stop(self):

		debug_task = self.__registry__.registry_storage().started_task(
			'com.binblob.wasp-launcher.launcher.web_debugger::connection'
		)
		if debug_task is not None:
			debug_task.stop()

		WLauncherGlobals.tornado_service = None
		WLauncherGlobals.tornado_io_loop = None
		WLauncherGlobals.wasp_web_service = None

		WLauncherGlobals.log.info('Web-service finalized')


class WLauncherWebServiceStart(WLauncherTask):

	__registry_tag__ = 'com.binblob.wasp-launcher.launcher.web_service::start'
	""" Task tag
	"""

	__dependency__ = [
		'com.binblob.wasp-launcher.launcher.log::log_setup',
		'com.binblob.wasp-launcher.launcher.config::read_config',
		'com.binblob.wasp-launcher.launcher.app_loader::load',
		'com.binblob.wasp-launcher.launcher.web_service::pre_init',
		'com.binblob.wasp-launcher.launcher.broker::broker_start',
		'com.binblob.wasp-launcher.launcher.web_templates::load'
	]

	def start(self):
		self.setup_app_presenters()

		WLauncherGlobals.tornado_service.listen(8888)
		WLauncherGlobals.tornado_io_loop.start()

		WLauncherGlobals.log.info('Web-service is started')

	def stop(self):
		WLauncherGlobals.tornado_io_loop.stop()
		WLauncherGlobals.log.info('Web-service is stopped')

	def setup_app_presenters(self):

		presenters_count = 0
		for app_name in WLauncherGlobals.apps_registry.registry_storage().tags():
			app = WLauncherGlobals.apps_registry.registry_storage().tasks(app_name)
			if issubclass(app, WLauncherWebAppDescriptor) is True:
				for presenter in app.public_presenters():
					WLauncherGlobals.wasp_web_service.add_presenter(presenter)
					presenters_count += 1
				for route in app.public_routes():
					WLauncherGlobals.wasp_web_service.route_map().append(route)

		WLauncherGlobals.log.info('Web-application %i presenters were set' % presenters_count)

		error_presenter_name = WLauncherGlobals.config['wasp-launcher::web']['error_presenter']
		if WLauncherGlobals.wasp_web_service.presenter_collection().has(error_presenter_name) is True:
			error_presenter = WLauncherGlobals.wasp_web_service.presenter_collection().presenter(
				error_presenter_name
			)
			WLauncherGlobals.wasp_web_service.route_map().set_error_presenter(error_presenter)
			WLauncherGlobals.log.info('Presenter "%s" set as error presenter' % error_presenter_name)

		# TODO: load routes from config
		# TODO: add auto routes
