# -*- coding: utf-8 -*-
# wasp_launcher/tasks/launcher/registry.py
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

from wasp_general.task.dependency import WTaskDependencyRegistry, WTaskDependencyRegistryStorage, WDependentTask
from wasp_general.task.base import WTask
from wasp_general.task.sync import WSyncTask
from wasp_general.task.thread import WThreadTask


class WLauncherRegistry(WTaskDependencyRegistry):
	""" Main registry to keep tasks responded to the launcher starting
	"""
	__registry_storage__ = WTaskDependencyRegistryStorage()
	""" Default storage for this type of registry
	"""


class WLauncherBaseTask(WTask, metaclass=WDependentTask):
	""" Base class for launcher tasks. This class defines link to the registry, which holds every launcher tasks
	"""

	__registry__ = WLauncherRegistry
	""" Link to registry
	"""


class WLauncherTask(WLauncherBaseTask, WSyncTask, metaclass=WDependentTask):
	""" Launcher task, that executes in foreground
	"""
	pass


class WLauncherThreadedTask(WLauncherBaseTask, WThreadTask, metaclass=WDependentTask):
	""" Launcher task, that executes in a separate thread
	"""
	pass
