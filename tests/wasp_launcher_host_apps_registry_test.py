# -*- coding: utf-8 -*-

import pytest

from wasp_launcher.apps import WHostAppRegistry, WSyncHostApp

from wasp_general.task.dependency import WTaskDependencyRegistry, WTaskDependencyRegistryStorage, WDependentTask
from wasp_general.task.sync import WSyncTask


class TestWAppRegistry:

	def test_implementation(self):
		assert(isinstance(WHostAppRegistry(), WTaskDependencyRegistry) is True)
		assert(isinstance(WHostAppRegistry.__registry_storage__, WTaskDependencyRegistryStorage) is True)


class TestWLauncherTask:

	def test_implementation(self):
		with pytest.raises(TypeError):
			WSyncHostApp()

		assert(issubclass(WSyncHostApp, WSyncTask) is True)
		assert(isinstance(WSyncHostApp, WDependentTask) is True)
		assert(WSyncHostApp.__registry__ == WHostAppRegistry)
