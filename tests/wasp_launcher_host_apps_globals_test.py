# -*- coding: utf-8 -*-

from wasp_launcher.host_apps.globals import WLauncherGlobals


def test_globals():
	assert(WLauncherGlobals.log is None)
	assert(WLauncherGlobals.config is None)
