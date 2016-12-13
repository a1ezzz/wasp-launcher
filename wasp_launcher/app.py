# -*- coding: utf-8 -*-
# wasp_launcher/app.py
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

from wasp_general.task.thread import WThreadTask
from wasp_general.task.dependency import WTaskDependencyRegistry, WTaskDependencyRegistryStorage


class WLauncherAppRegistry(WTaskDependencyRegistry):
	__registry_storage__ = WTaskDependencyRegistryStorage()


class WLauncherAppDescriptor(WThreadTask):

	__registry__ = WLauncherAppRegistry
	__registry_tag__ = '::wasp_launcher::app'

	@classmethod
	def name(cls):
		return cls.__registry_tag__

	@classmethod
	def description(cls):
		return None
