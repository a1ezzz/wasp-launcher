# -*- coding: utf-8 -*-

import pytest

from wasp_launcher.tasks.launcher.registry import WLauncherRegistry, WLauncherTask

from wasp_general.task.dependency import WTaskDependencyRegistry, WTaskDependencyRegistryStorage, WDependentTask
from wasp_general.task.sync import WSyncTask


class TestWLauncherRegistry:

	def test_implementation(self):
		assert(isinstance(WLauncherRegistry(), WTaskDependencyRegistry) is True)
		assert(isinstance(WLauncherRegistry.__registry_storage__, WTaskDependencyRegistryStorage) is True)


class TestWLauncherTask:

	def test_implementation(self):
		with pytest.raises(TypeError):
			WLauncherTask()

		assert(issubclass(WLauncherTask, WSyncTask) is True)
		assert(isinstance(WLauncherTask, WDependentTask) is True)
		assert(WLauncherTask.__registry__ == WLauncherRegistry)
