# -*- coding: utf-8 -*-
# wasp_launcher/loader.py
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

import re
from importlib import import_module

from wasp_general.verify import verify_type, verify_value

from wasp_launcher.core import WAppsGlobals


class WClassLoader:

	__item_section_pattern__ = '^%s::(.+)$'

	@verify_type(section_prefix=str, target_class=type)
	@verify_value(section_prefix=lambda x: len(x) > 0, tag_fn=lambda x: x is None or callable(x))
	def __init__(self, section_prefix, target_class, tag_fn=None):
		self.__section_re = re.compile(self.__item_section_pattern__ % section_prefix)
		self.__target_class = target_class
		self.__tag_fn = tag_fn

	@verify_type(section_name=str)
	@verify_value(section_name=lambda x: len(x) > 0)
	def section_matched(self, section_name):
		result = self.__section_re.search(section_name)
		if result is not None:
			return result.group(1)

	def target_class(self):
		return self.__target_class

	@verify_type(cls=type, tag=str)
	@verify_value(tag=lambda x: len(x) > 0)
	def check_tag(self, cls, tag):
		if self.__tag_fn is not None:
			cls_tag = self.__tag_fn(cls)
			if cls_tag != tag:
				raise RuntimeError(
					'Misconfiguration spotted. Class and configuration have '
					'different tags: "%s" and "%s"' %
					(cls_tag, tag)
				)

	@verify_value(callback=lambda x: callable(x))
	def load(self, callback):

		for section_name in WAppsGlobals.config.sections():
			item_tag = self.section_matched(section_name)
			if item_tag is None:
				continue

			if WAppsGlobals.config.getboolean(section_name, 'enabled') is False:
				continue

			module_name = WAppsGlobals.config[section_name]['module_name']
			cls_name = WAppsGlobals.config[section_name]['class_name']
			item_module = import_module(module_name)
			if hasattr(item_module, cls_name) is False:
				raise RuntimeError(
					'Module "%s" does not have the specified class %s' %
					(module_name, cls_name)
				)
			item_cls = getattr(item_module, cls_name)
			if issubclass(item_cls, self.target_class()) is False:
				raise RuntimeError(
					'Invalid class (%s) was specified in configuration in section "%s". '
					'Expected - %s' % (cls_name, section_name, self.target_class().__name__)
				)

			self.check_tag(item_cls, item_tag)

			callback(section_name, item_tag, item_cls)
