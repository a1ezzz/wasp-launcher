# -*- coding: utf-8 -*-
# wasp_launcher/apps/templates.py
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

import os

from abc import ABCMeta, abstractmethod
from mako.lookup import TemplateCollection
from mako.exceptions import TemplateLookupException
from importlib import import_module
from inspect import isfunction, isclass
from tempfile import TemporaryDirectory


from wasp_general.verify import verify_type, verify_subclass, verify_value

from wasp_general.template import WTemplateFile, WTemplate, WTemplateText, WTemplateLookup

from wasp_launcher.core import WSyncApp, WTemplatesSource, WAppsGlobals


class WTemplateSearcherProto(metaclass=ABCMeta):

	__separator__ = '::'

	@abstractmethod
	def replace(self, view_name, view):
		raise NotImplementedError('This method is abstract')

	@abstractmethod
	def has(self, view_name):
		raise NotImplementedError('This method is abstract')

	@abstractmethod
	def get(self, view_path, **template_args):
		raise NotImplementedError('This method is abstract')


class WBasicTemplateSearcher(WTemplateSearcherProto):

	def __init__(self):
		self.__views = {}

	def has(self, view_name):
		return view_name in self.__views.keys()

	def search(self, view_name):
		if self.has(view_name):
			return self.__views[view_name]

	def replace(self, view_name, view):
		self.__views[view_name] = view

	@verify_type(view_path=(list, tuple))
	def get(self, view_path, **template_args):
		if len(view_path) == 0:
			raise TemplateLookupException('Empty path')

		search = self.search(view_path[0])
		if search is not None:
			if isinstance(search, WTemplateSearcherProto) is True:
				return search.get(view_path[1:], **template_args)
			elif isinstance(search, WTemplate) is True:
				return search
			raise RuntimeError('Invalid lookup object')

		raise TemplateLookupException('No such template: %s' % (str(view_path)))

	@verify_type(view_path=str)
	def get_by_uri(self, view_path):
		return self.get(view_path.split(WTemplateSearcherProto.__separator__))


class WTemplateSearcherBase(WBasicTemplateSearcher, metaclass=ABCMeta):

	class Handler(WBasicTemplateSearcher, metaclass=ABCMeta):

		@verify_subclass(template_source=WTemplatesSource)
		def __init__(self, template_source):
			WBasicTemplateSearcher.__init__(self)
			self.__template_source = template_source

		def template_source(self):
			return self.__template_source

	@verify_type(template_source=WTemplatesSource)
	def add_template_source(self, template_source):
		obj = self.handler_class()(template_source.__class__)
		self.replace(template_source.name(), obj)

	@abstractmethod
	def handler_class(self):
		raise NotImplementedError('This method is abstract')


class WSearcherFileHandler(WTemplateSearcherBase.Handler):

	def template_directory(self):
		return None

	def filename(self, view_path):
		template_dir = self.template_directory()
		return os.path.join(template_dir, *view_path) if template_dir is not None else None

	def has(self, view_name):

		filename = self.filename([view_name])
		if filename is None:
			return False

		return os.path.exists(filename)

	def get(self, view_path, **template_args):
		if isinstance(view_path, (list, tuple)) is False:
			return None
		if len(view_path) == 0:
			return None

		path = self.filename(view_path)
		if os.path.isfile(path):
			return WTemplateFile(path, **template_args)
		else:
			raise TemplateLookupException('No such template: ' + str(view_path))


class WMakoTemplateSearcher(WTemplateSearcherBase):

	class Handler(WSearcherFileHandler):

		def template_directory(self):
			return self.template_source().template_path()

	def handler_class(self):
		return WMakoTemplateSearcher.Handler


class WStaticFileSearcher(WTemplateSearcherBase):

	class Handler(WSearcherFileHandler):

		def template_directory(self):
			return self.template_source().static_files_path()

	def handler_class(self):
		return WStaticFileSearcher.Handler


class WPyTemplateSearcher(WTemplateSearcherBase):

	class PyHandler(WTemplateSearcherBase.Handler):

		class PyModuleHandler(WBasicTemplateSearcher):
			def __init__(self, module):
				WBasicTemplateSearcher.__init__(self)
				self.__module = module
				for obj_name in dir(module):
					obj = getattr(module, obj_name)
					if isfunction(obj) or isclass(obj):
						self.replace(obj_name, obj)

			def get(self, view_path, **template_args):
				if isinstance(view_path, (list, tuple)) is False:
					return

				if len(view_path) != 1:
					return

				fn = self.search(view_path[0])
				if isfunction(fn):
					return WTemplateText(fn(), **template_args)
				elif isclass(fn):
					return WTemplateText(fn()(), **template_args)

				raise TemplateLookupException('No such template: %s' % (str(view_path)))

		def module_name(self, view_name):
			m = self.template_source().py_templates_package()
			if m is not None:
				return m + '.' + view_name
			raise TemplateLookupException('No such template: %s' % view_name)

		def has(self, view_name):
			try:
				import_module(self.module_name(view_name))
				return True
			except ImportError:
				return False

		def get(self, view_path, **template_args):
			if isinstance(view_path, (list, tuple)) is False:
				return None

			if len(view_path) < 1:
				return None

			if len(view_path) < 2:
				return None

			m = import_module(self.module_name(view_path[0]))
			h = WPyTemplateSearcher.PyHandler.PyModuleHandler(m)
			result = h.get([view_path[1]])
			return result

	def handler_class(self):
		return WPyTemplateSearcher.PyHandler


class WAgentTemplateSearcher(TemplateCollection, WBasicTemplateSearcher):

	def __init__(self):
		TemplateCollection.__init__(self)
		WBasicTemplateSearcher.__init__(self)
		self.__mako_searcher = WMakoTemplateSearcher()
		self.__static_file_searcher = WStaticFileSearcher()
		self.__py_searcher = WPyTemplateSearcher()

		self.replace('mako', self.__mako_searcher)
		self.replace('static-file', self.__static_file_searcher)
		self.replace('py', self.__py_searcher)

		self._module_directory = None
		if WAppsGlobals.config.getboolean('wasp-launcher::web:templates', 'modules_directory') is True:
			self._module_directory = TemporaryDirectory(suffix='.wasp_mako')

		self._template_encoding = None
		config_encoding = WAppsGlobals.config['wasp-launcher::web:templates']['input_encoding']
		if len(config_encoding) > 0:
			self._template_encoding = config_encoding

	@verify_type(template_source=WTemplatesSource)
	def add_template_source(self, template_source):
		self.__mako_searcher.add_template_source(template_source)
		self.__static_file_searcher.add_template_source(template_source)
		self.__py_searcher.add_template_source(template_source)

	@verify_type(uri=str)
	@verify_value(uri=lambda x: len(x) > 0)
	def get_template(self, uri, relativeto=None):
		return self.get(
			uri.strip().split(WTemplateSearcherProto.__separator__),
			lookup=self,
			module_directory=self._module_directory.name,
			input_encoding=self._template_encoding
		).template()

	def lookup(self, uri):
		result = WTemplateLookup(uri, self)
		return result


class WTemplateLookupApp(WSyncApp):

	__registry_tag__ = 'com.binblob.wasp-launcher.apps.template-lookup'
	""" Task tag
	"""

	__dependency__ = ['com.binblob.wasp-launcher.apps.config']

	def start(self):
		WAppsGlobals.log.info('Web-templates is starting')
		WAppsGlobals.templates = WAgentTemplateSearcher()

	def stop(self):
		WAppsGlobals.log.info('Web-templates is stopping')
		WAppsGlobals.templates = None
