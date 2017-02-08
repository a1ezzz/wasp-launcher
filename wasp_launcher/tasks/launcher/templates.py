# -*- coding: utf-8 -*-
# wasp_launcher/tasks/launcher/templates.py
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

from abc import ABCMeta, abstractmethod
from mako.lookup import TemplateCollection
from mako.exceptions import TemplateLookupException
from importlib import import_module
from inspect import isfunction, isclass
from tempfile import TemporaryDirectory


from wasp_general.verify import verify_type, verify_subclass, verify_value

from wasp_network.web.template import WWebTemplateFile, WWebTemplate, WWebTemplateText, WWebTemplateLookup

from wasp_launcher.tasks.launcher.registry import WLauncherTask
from wasp_launcher.tasks.launcher.globals import WLauncherGlobals
from wasp_launcher.app import WLauncherWebAppDescriptor


class WLauncherTemplateSearcherProto(metaclass=ABCMeta):

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


class WLauncherBasicTemplateSearcher(WLauncherTemplateSearcherProto):

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
			if isinstance(search, WLauncherTemplateSearcherProto) is True:
				return search.get(view_path[1:])
			elif isinstance(search, WWebTemplate) is True:
				return search
			raise RuntimeError('Invalid lookup object')

		raise TemplateLookupException('No such template: %s' % (str(view_path)))

	@verify_type(view_path=str)
	def get_by_uri(self, view_path):
		return self.get(view_path.split(WLauncherTemplateSearcherProto.__separator__))


class WLauncherAppTemplateSearcher(WLauncherBasicTemplateSearcher, metaclass=ABCMeta):

	class Handler(WLauncherBasicTemplateSearcher, metaclass=ABCMeta):

		@verify_subclass(app_description=WLauncherWebAppDescriptor)
		def __init__(self, app_description):
			WLauncherBasicTemplateSearcher.__init__(self)
			self.__app_description = app_description

		def app_description(self):
			return self.__app_description

	def __init__(self):
		WLauncherBasicTemplateSearcher.__init__(self)

		for app_name in WLauncherGlobals.apps_registry.registry_storage().tags():
			app = WLauncherGlobals.apps_registry.registry_storage().tasks(app_name)
			if issubclass(app, WLauncherWebAppDescriptor) is True:
				obj = self.handler_class()(app)
				self.replace(app_name, obj)

	@abstractmethod
	def handler_class(self):
		raise NotImplementedError('This method is abstract')


class WSearcherFileHandler(WLauncherAppTemplateSearcher.Handler):

	def app_directory(self):
		return None

	def filename(self, view_path):
		app_dir = self.app_directory()
		return os.path.join(app_dir, *view_path) if app_dir is not None else None

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
			return WWebTemplateFile(path, **template_args)
		else:
			raise TemplateLookupException('No such template: ' + str(view_path))


class WMakoTemplateSearcher(WLauncherAppTemplateSearcher):

	class Handler(WSearcherFileHandler):

		def app_directory(self):
			return self.app_description().template_path()

	def handler_class(self):
		return WMakoTemplateSearcher.Handler


class WStaticFileSearcher(WLauncherAppTemplateSearcher):

	class Handler(WSearcherFileHandler):

		def app_directory(self):
			return self.app_description().static_files_path()

	def handler_class(self):
		return WStaticFileSearcher.Handler


class WPyTemplateSearcher(WLauncherAppTemplateSearcher):

	class PyHandler(WLauncherAppTemplateSearcher.Handler):

		class PyModuleHandler(WLauncherBasicTemplateSearcher):
			def __init__(self, module):
				WLauncherBasicTemplateSearcher.__init__(self)
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
					return WWebTemplateText(fn(), **template_args)
				elif isclass(fn):
					return WWebTemplateText(fn()(), **template_args)

				raise TemplateLookupException('No such template: %s' % (str(view_path)))

		def module_name(self, view_name):
			m = self.app_description().py_templates_package()
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


class WLauncherTemplateSearcher(TemplateCollection, WLauncherBasicTemplateSearcher):

	def __init__(self):
		TemplateCollection.__init__(self)
		WLauncherBasicTemplateSearcher.__init__(self)
		self.replace('mako', WMakoTemplateSearcher())
		self.replace('static-file', WStaticFileSearcher())
		self.replace('py', WPyTemplateSearcher())

		self._module_directory = None
		if WLauncherGlobals.config.getboolean('wasp-launcher::web:templates', 'modules_directory') is True:
			self._module_directory = TemporaryDirectory(suffix='.wasp_mako')

		self._template_encoding = None
		config_encoding = WLauncherGlobals.config['wasp-launcher::web:templates']['input_encoding']
		if len(config_encoding) > 0:
			self._template_encoding = config_encoding

	@verify_type(uri=str)
	@verify_value(uri=lambda x: len(x) > 0)
	def get_template(self, uri, relativeto=None):
		return self.get(
			uri.strip().split(WLauncherTemplateSearcherProto.__separator__),
			lookup_obj=self,
			module_directory=self._module_directory.name,
			template_encoding=self._template_encoding
		)

	def lookup(self, uri):
		return WWebTemplateLookup(uri, self)


class WLauncherWebTemplates(WLauncherTask):

	__registry_tag__ = 'com.binblob.wasp-launcher.launcher.web_templates::load'
	""" Task tag
	"""

	__dependency__ = [
		'com.binblob.wasp-launcher.launcher.log::log_setup',
		'com.binblob.wasp-launcher.launcher.config::read_config',
		'com.binblob.wasp-launcher.launcher.app_loader::load',
		'com.binblob.wasp-launcher.launcher.web_service::pre_init'
	]

	def start(self):
		WLauncherGlobals.templates = WLauncherTemplateSearcher()
		WLauncherGlobals.log.info('Web-templates is started')

	def stop(self):
		WLauncherGlobals.templates = None
		WLauncherGlobals.log.info('Web-templates is stopped')
