# -*- coding: utf-8 -*-

import pytest
import logging

from wasp_launcher.log import WLauncherLogSetup
from wasp_launcher.launcher_registry import WLauncherTask
from wasp_launcher.globals import WLauncherGlobals


@pytest.fixture
def global_log(request):
	def fin():
		WLauncherGlobals.log = None
	request.addfinalizer(fin)


class TestWLauncherLogSetup:

	@pytest.mark.usefixtures('global_log')
	def test_task(self):
		assert(isinstance(WLauncherLogSetup(), WLauncherTask) is True)
		task = WLauncherLogSetup.start_dependent_task()
		assert(isinstance(WLauncherGlobals.log, logging.Logger) is True)
		task.stop()
		assert(WLauncherGlobals.log is None)
