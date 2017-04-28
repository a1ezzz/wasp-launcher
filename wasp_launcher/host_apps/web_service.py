# -*- coding: utf-8 -*-
# wasp_launcher/host_apps/web_service.py
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

from abc import ABCMeta

from tornado.ioloop import IOLoop
import tornado.web
import tornado.httpserver

from wasp_general.verify import verify_type, verify_value

from wasp_general.network.web.service import WWebService, WWebTargetRoute, WWebEnhancedPresenter, WWebPresenterFactory
from wasp_general.network.web.proto import WWebRequestProto
from wasp_general.network.web.tornado import WTornadoRequestHandler
from wasp_general.network.web.template import WWebTemplateResponse

from wasp_launcher.apps import WSyncHostApp, WThreadedHostApp, WAppsGlobals
from wasp_launcher.host_apps.web_debugger import WLauncherWebDebugger


class WLauncherWebPresenter(WWebEnhancedPresenter, metaclass=ABCMeta):

	@verify_type(request=WWebRequestProto, target_route=WWebTargetRoute, service=WWebService)
	def __init__(self, request, target_route, service):
		WWebEnhancedPresenter.__init__(self, request, target_route, service)
		self._context = {}

	@verify_type(template_id=str)
	@verify_value(template_id=lambda x: len(x) > 0)
	def __template__(self, template_id):
		return WAppsGlobals.templates.lookup(template_id)

	@verify_type(template_id=str)
	@verify_value(template_id=lambda x: len(x) > 0)
	def __template_response__(self, template_id):
		return WWebTemplateResponse(self.__template__(template_id), context=self._context)


class WLauncherPresenterFactory(WWebPresenterFactory):

	def __init__(self):
		WWebPresenterFactory.__init__(self)
		self._add_constructor(
			WLauncherWebPresenter, WWebPresenterFactory.enhanced_presenter_constructor
		)


class WLauncherWebServicePreInitApp(WSyncHostApp):
	""" Task that prepare web-service
	"""

	__registry_tag__ = 'com.binblob.wasp-launcher.launcher.web_service::pre_init'
	""" Task tag
	"""

	__dependency__ = [
		'com.binblob.wasp-launcher.launcher.app_loader::load'
	]
	""" Task dependency
	"""

	def start(self):
		WAppsGlobals.wasp_web_service = WWebService(
			factory=WLauncherPresenterFactory, debugger=WLauncherWebDebugger()
		)
		WAppsGlobals.tornado_io_loop = IOLoop()

		WAppsGlobals.tornado_service = tornado.httpserver.HTTPServer(
			tornado.web.Application([
				(r".*", WTornadoRequestHandler.__handler__(WAppsGlobals.wasp_web_service))
			]), io_loop=WAppsGlobals.tornado_io_loop
		)

		WAppsGlobals.log.info('Web-service is ready to start (initialized)')

		if WAppsGlobals.config["wasp-launcher::web:debug"]["mode"].lower() in ['on', 'on error']:
			self.__registry__.start_task('com.binblob.wasp-launcher.launcher.web_debugger::connection')

	def stop(self):

		debug_task = self.__registry__.registry_storage().started_task(
			'com.binblob.wasp-launcher.launcher.web_debugger::connection'
		)
		if debug_task is not None:
			debug_task.stop()

		WAppsGlobals.tornado_service = None
		WAppsGlobals.tornado_io_loop = None
		WAppsGlobals.wasp_web_service = None

		WAppsGlobals.log.info('Web-service finalized')


class WWebServiceStartApp(WThreadedHostApp):

	__registry_tag__ = 'com.binblob.wasp-launcher.launcher.web_service::start'
	""" Task tag
	"""

	__dependency__ = [
		'com.binblob.wasp-launcher.launcher.broker::broker_start',
		'com.binblob.wasp-launcher.launcher.web_templates::load'
	]

	def start(self):
		self.setup_app_presenters()

		WAppsGlobals.tornado_service.listen(8888)
		WAppsGlobals.log.info('Web-service is starting')
		WAppsGlobals.tornado_io_loop.start()

	def stop(self):
		WAppsGlobals.tornado_io_loop.stop()
		WAppsGlobals.log.info('Web-service is stopped')

	def setup_app_presenters(self):
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
