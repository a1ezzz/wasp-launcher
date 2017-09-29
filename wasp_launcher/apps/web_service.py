# -*- coding: utf-8 -*-
# wasp_launcher/apps/web_service.py
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

import tornado.web
import tornado.httpserver

from wasp_general.network.service import WLoglessIOLoop
from wasp_general.network.primitives import WIPV4SocketInfo
from wasp_general.network.web.service import WWebService, WWebPresenterFactory
from wasp_general.network.web.tornado import WTornadoRequestHandler

from wasp_launcher.core import WSyncApp, WThreadedApp, WAppsGlobals, WWebPresenter, WWebApp
from wasp_launcher.apps.web_debugger import WWebAppDebugger


class WLauncherWebPresenterFactory(WWebPresenterFactory):

	def __init__(self):
		WWebPresenterFactory.__init__(self)
		self._add_constructor(
			WWebPresenter, WWebPresenterFactory.enhanced_presenter_constructor
		)


class WWebServiceInitApp(WSyncApp):
	""" Task that prepare web-service
	"""

	__registry_tag__ = 'com.binblob.wasp-launcher.apps.web::init'
	""" Task tag
	"""

	__dependency__ = [
		'com.binblob.wasp-launcher.apps.config'
	]
	""" Task dependency
	"""

	def start(self):
		WAppsGlobals.log.info('Web-service is initializing')

		debugger = WAppsGlobals.config["wasp-launcher::web:debug"]["mode"].lower() in ['on', 'on error']

		debugger_app_section = \
			'wasp-launcher::applications::com.binblob.wasp-launcher.apps.web-debugger::datastore'
		debugger_app_enabled = WAppsGlobals.config.getboolean(debugger_app_section, 'enabled')
		debugger_app_auto_start = WAppsGlobals.config.getboolean(debugger_app_section, 'auto_start')

		if debugger is True:
			if debugger_app_enabled is False or debugger_app_auto_start is False:
				WAppsGlobals.log.error(
					'Web debugger service is disabled (and/or removed from auto start). '
					'Debug of web-session is disabled'
				)
				debugger = False

		WAppsGlobals.wasp_web_service = WWebService(
			factory=WLauncherWebPresenterFactory,
			debugger=(WWebAppDebugger() if debugger is True else None)
		)

		WAppsGlobals.tornado_io_loop = WLoglessIOLoop()

		WAppsGlobals.tornado_service = tornado.httpserver.HTTPServer(
			tornado.web.Application([
				(r".*", WTornadoRequestHandler.__handler__(WAppsGlobals.wasp_web_service))
			]),
			io_loop=WAppsGlobals.tornado_io_loop
		)

	def stop(self):
		WAppsGlobals.log.info('Web-service is finalizing')

		WAppsGlobals.tornado_service = None
		WAppsGlobals.tornado_io_loop = None
		WAppsGlobals.wasp_web_service = None


class WWebServiceApp(WThreadedApp):

	__registry_tag__ = 'com.binblob.wasp-launcher.apps.web::start'
	""" Task tag
	"""

	__dependency__ = [
		'com.binblob.wasp-launcher.apps.model-load'
	]

	__dynamic_dependency__ = WWebApp

	__thread_name__ = "WWebServiceApp"

	def thread_started(self):
		self.setup_presenters()

		info = WIPV4SocketInfo.parse_socket_info(
			WAppsGlobals.config['wasp-launcher::web']['bind_address']
		)
		if info.port() is None:
			raise RuntimeError('Invalid bind address in the configuration')

		WAppsGlobals.tornado_service.listen(int(info.port()), address=str(info.address()))
		WAppsGlobals.log.info('Web-service is starting')
		WAppsGlobals.tornado_io_loop.start()

	def thread_stopped(self):
		if WAppsGlobals.tornado_io_loop is not None:
			WAppsGlobals.tornado_io_loop.stop()
			WAppsGlobals.log.info('Web-service was stopped')

	@classmethod
	def setup_presenters(cls):
		presenters_count = len(WAppsGlobals.wasp_web_service.presenter_collection())
		WAppsGlobals.log.info('Web-application presenters loaded: %i' % presenters_count)

		error_presenter_name = WAppsGlobals.config['wasp-launcher::web']['error_presenter']
		if WAppsGlobals.wasp_web_service.presenter_collection().has(error_presenter_name) is True:
			error_presenter = WAppsGlobals.wasp_web_service.presenter_collection().presenter(
				error_presenter_name
			)
			WAppsGlobals.wasp_web_service.route_map().set_error_presenter(error_presenter)
			WAppsGlobals.log.info('Presenter "%s" set as error presenter' % error_presenter_name)
		elif len(error_presenter_name) > 0:
			WAppsGlobals.log.warn(
				'Presenter "%s" can\'t be set as error presenter (wasn\'t found).' %
				error_presenter_name
			)

		# TODO: load routes from config
		# TODO: add auto routes
