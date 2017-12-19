# -*- coding: utf-8 -*-
# wasp_launcher/apps/web/wasp.py
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
# TODO: develop "LightPresenter"
# TODO: develop I18NPresenter


# noinspection PyUnresolvedReferences
from wasp_launcher.version import __author__, __version__, __credits__, __license__, __copyright__, __email__
# noinspection PyUnresolvedReferences
from wasp_launcher.version import __status__

import os

from wasp_general.mime import mime_type
from wasp_general.verify import verify_type, verify_value

from wasp_general.network.web.headers import WHTTPHeaders
from wasp_general.network.web.response import WWebResponse
from wasp_general.network.web.service import WWebEnhancedPresenter, WSimpleErrorPresenter
from wasp_general.network.web.proto import WWebPresenter
from wasp_general.template import WTemplateText
from wasp_general.network.web.template_response import WWebTemplateResponse
from wasp_general.network.web.service import WWebRoute

from wasp_launcher.core import WWebApp


class WRedirectPresenter(WWebPresenter):

	def index(self, url):
		return WWebResponse(status=307, headers=WHTTPHeaders(**{'Location': url}))

	@classmethod
	def __presenter_name__(cls):
		return 'com.binblob.wasp-launcher.apps.wasp-basic.redirect-presenter'


class WStaticFilesPresenter(WWebEnhancedPresenter):

	template = '''<HTML>

<HEAD>
	<TITLE>${static_title}</TITLE>
</HEAD>

<BODY marginheight="30" marginwidth="30">

<TABLE cellpadding="0" cellspacing="0">
	% for url in urls:
	<TR><TD><A href=${url[0]}>${url[1]}</A></TD></TR>
	% endfor
</TABLE>

</BODY>

</HTML>'''

	@staticmethod
	def __normalize_dir(dir_path):
		if len(dir_path):
			index = len(dir_path) - 1
			if dir_path[index] == os.sep:
				dir_path = dir_path[:index]
				return WStaticFilesPresenter.__normalize_dir(dir_path)
		return dir_path

	def __list_template__(self):
		return WStaticFilesPresenter.template

	def __list_directory(self, list_dir, basedir):

		list_dir = WStaticFilesPresenter.__normalize_dir(list_dir)
		basedir = WStaticFilesPresenter.__normalize_dir(basedir)

		if os.pardir in list_dir:
			return WWebResponse(status=403)

		context = {'static_title': 'Directory %s' % list_dir, 'urls': []}

		if list_dir != basedir:
			route = self.__target_route__().route()
			link = route.url_for(path=os.path.dirname(list_dir[len(basedir):]))
			context['urls'].append((link, os.pardir))

		files = []
		dirs = []
		for entry in os.listdir(list_dir):
			if os.path.isdir(os.path.join(list_dir, entry)):
				dirs.append(entry)
			else:
				files.append(entry)

		for entry in dirs:
			link = self.__request__().path() + '/' + entry
			context['urls'].append((link, entry))

		for entry in files:
			link = self.__request__().path() + '/' + entry
			context['urls'].append((link, entry))

		return WWebTemplateResponse(WTemplateText(self.__list_template__()), context=context)

	@verify_type(listdir=bool)
	def index(self, path, basedir, listdir=False):
		file = os.path.join(basedir, path)

		if not os.path.exists(file):
			return WWebResponse(status=404)

		if os.path.isdir(file):
			if listdir is True:
				return self.__list_directory(file, basedir)
			else:
				return WWebResponse(status=403)

		if os.path.islink(file):
			content_type = mime_type(os.path.realpath(file))
		else:
			content_type = mime_type(file)

		return WWebResponse(
			status=200,
			headers=WHTTPHeaders(**{'Content-Type': content_type}),
			response_data=open(file, 'rb').read()
		)

	@classmethod
	def __presenter_name__(cls):
		return 'com.binblob.wasp-launcher.apps.wasp-basic.staticfiles-presenter'

	@classmethod
	def __public_routes__(cls):
		return [
			WWebRoute(
				'/static.wasp-basic.angular{path:"/?(.*)"}',
				'com.binblob.wasp-launcher.apps.wasp-basic.staticfiles-presenter',
				basedir=os.path.join(os.path.dirname(__file__), '..', 'static', 'angular'),
				listdir=False
			),
			WWebRoute(
				'/static.wasp-basic.bootstrap{path:"/?(.*)"}',
				'com.binblob.wasp-launcher.apps.wasp-basic.staticfiles-presenter',
				basedir=os.path.join(os.path.dirname(__file__), '..', 'static', 'bootstrap'),
				listdir=False
			)
		]


class WErrorPresenter(WSimpleErrorPresenter):

	template = '''<HTML>
<%def name="show_messages(messages)">
% for message in messages:
<DIV style="margin-bottom: 20px">
	<H3 style="display: inline;">${message}:</H3>
	${messages [message]}
</DIV>
% endfor
</%def>
<HEAD>
	<TITLE>${error_title}</TITLE>
</HEAD>

<BODY marginheight="0" marginwidth="0">

<TABLE width="100%" height="100%" cellpadding="0" cellspacing="20">
	<TR>
		<TD width="100%" valign="top" align="center">
			<DIV style="margin: 30px" border="1">
				<H2>${error_header}</H2>
			</DIV>

			${show_messages(error_messages)}

			<DIV style="margin: 60px" border="1">
				<HR width="100%" style="border: 1px solid black;">
				<P align="left" style="font-size: smaller">${error_footer}</P>
			</DIV>
		</TD>

	</TR>
</TABLE>

</BODY>
</HTML>'''

	def __error_template__(self):
		return WErrorPresenter.template

	@verify_type(code=int)
	@verify_value(code=lambda x: x > 0)
	def error_code(self, code):
		"""
		:param code:
		:return:
		"""

		context = {
			'error_title': "Damn error page %i" % code,
			'error_header': "What has happened?",
			'error_footer': "WHY!?!?!",
			'error_messages': {
				('Error %i' % code): self.__message__(code)
			}
		}
		return WWebTemplateResponse(WTemplateText(self.__error_template__()), context=context)

	@classmethod
	def __presenter_name__(cls):
		return 'com.binblob.wasp-launcher.apps.wasp-basic.error-presenter'


class WWaspBasicApps(WWebApp):

	__registry_tag__ = 'com.binblob.wasp-launcher.apps.web.wasp-basic'

	@classmethod
	def public_presenters(cls):
		return [WRedirectPresenter, WStaticFilesPresenter, WErrorPresenter]
