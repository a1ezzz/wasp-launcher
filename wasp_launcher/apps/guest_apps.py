# -*- coding: utf-8 -*-
# wasp_launcher/apps/guest_apps.py
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

# TODO: document the code
# TODO: write tests for the code

# noinspection PyUnresolvedReferences
from wasp_launcher.version import __author__, __version__, __credits__, __license__, __copyright__, __email__
# noinspection PyUnresolvedReferences
from wasp_launcher.version import __status__

from wasp_launcher.core import WSyncApp, WGuestApp, WAppsGlobals, WGuestAppRegistry
from wasp_launcher.loader import WClassLoader


class WGuestAppStarter(WSyncApp):

	__registry_tag__ = 'com.binblob.wasp-launcher.app.guest-apps'
	__dependency__ = [
		'com.binblob.wasp-launcher.app.web::init',
		'com.binblob.wasp-launcher.app.broker::init',
		'com.binblob.wasp-launcher.app.scheduler::init'
	]

	__guest_app_section_prefix__ = 'wasp-launcher::applications_guest'

	def start(self):
		WAppsGlobals.apps_registry = WGuestAppRegistry
		WAppsGlobals.apps_registry.clear()
		WAppsGlobals.started_apps.clear()

		apps_count = 0
		start_apps = []
		loader = WClassLoader(self.__guest_app_section_prefix__, WGuestApp, tag_fn=lambda x: x.name())

		def callback(section_name, item_tag, item_cls):
			WAppsGlobals.apps_registry.add(item_cls)
			if WAppsGlobals.config.getboolean(section_name, 'auto_start') is True:
				start_apps.append(item_tag)

		loader.load(callback)

		WAppsGlobals.log.info('Available local applications: %i' % apps_count)

		for app_name in start_apps:
			app = WAppsGlobals.apps_registry.registry_storage().tasks(app_name)
			WAppsGlobals.log.info('Starting "%s" application and its dependencies' % app_name)
			WAppsGlobals.apps_registry.start_task(app_name)
			WAppsGlobals.started_apps.append(app)
			WAppsGlobals.log.info('Application "%s" started' % app_name)

	def stop(self):
		for app_name in [x.name() for x in WAppsGlobals.started_apps]:
			WAppsGlobals.log.info('Stopping "%s" application and its dependencies' % app_name)
			WAppsGlobals.apps_registry.stop_task(app_name)
		WAppsGlobals.started_apps.clear()
		WAppsGlobals.apps_registry.clear()
