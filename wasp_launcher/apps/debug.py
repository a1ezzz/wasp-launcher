# -*- coding: utf-8 -*-
# wasp_launcher/apps/debug.py
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

import os

from wasp_network.web.headers import WHTTPHeaders
from wasp_network.web.response import WWebResponse
from wasp_network.web.service import WWebRoute, WWebEnhancedPresenter, WSimpleErrorPresenter
from wasp_network.web.proto import WWebPresenter
from wasp_network.web.template import WWebTemplateText, WWebTemplateResponse


from wasp_launcher.app import WLauncherWebAppDescriptor
from wasp_launcher.tasks.launcher.globals import WLauncherGlobals


class WDebugPresenter(WWebEnhancedPresenter):

	def index(self):
		context = {}
		template = WLauncherGlobals.templates.lookup('mako::com.binblob.wasp-launcher.apps.wasp-debug::test.mako')
		print('FOUND TEMPLATE:' + str(template.template()))
		return WWebTemplateResponse(template, context=context)

	@classmethod
	def __presenter_name__(cls):
		return 'com.binblob.wasp-launcher.apps.wasp-debug.debug-presenter'

	@classmethod
	def __public_routes__(cls):
		return [
			WWebRoute('/apps.wasp-debug.debug/', cls.__presenter_name__())
		]


class WWaspDebugApps(WLauncherWebAppDescriptor):

	__registry_tag__ = 'com.binblob.wasp-launcher.apps.wasp-debug'

	def start(self):
		pass

	def stop(self):
		pass

	@classmethod
	def public_presenters(cls):
		return [WDebugPresenter]

	@classmethod
	def template_path(cls):
		return os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'templates', 'debug'))
