# -*- coding: utf-8 -*-

import pytest
import logging

from wasp_launcher.apps.log import WLogApp
from wasp_launcher.core import WSyncApp, WAppsGlobals


@pytest.fixture
def fin_log(request):
	def fin():
		WAppsGlobals.log = None
	request.addfinalizer(fin)


class TestWLogHostApp:

	@pytest.mark.usefixtures('fin_log')
	def test_app(self):
		assert(isinstance(WLogHostApp(), WSyncHostApp) is True)
		app = WLogHostApp.start_dependent_task()
		assert(isinstance(WAppsGlobals.log, logging.Logger) is True)
		app.stop()
		assert(WAppsGlobals.log is None)
