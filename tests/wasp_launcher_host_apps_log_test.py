# -*- coding: utf-8 -*-

import pytest
import logging

from wasp_launcher.host_apps.log import WLauncherLogSetup
from wasp_launcher.host_apps.registry import WLauncherTask
from wasp_launcher.host_apps.globals import WLauncherGlobals


@pytest.fixture
def fin_log(request):
	def fin():
		WLauncherGlobals.log = None
	request.addfinalizer(fin)


class TestWLauncherLogSetup:

	@pytest.mark.usefixtures('fin_log')
	def test_task(self):
		assert(isinstance(WLauncherLogSetup(), WLauncherTask) is True)
		task = WLauncherLogSetup.start_dependent_task()
		assert(isinstance(WLauncherGlobals.log, logging.Logger) is True)
		task.stop()
		assert(WLauncherGlobals.log is None)
