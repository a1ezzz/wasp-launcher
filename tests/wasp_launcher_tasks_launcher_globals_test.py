# -*- coding: utf-8 -*-

from wasp_launcher.globals import WLauncherGlobals


def test_globals():
	assert(WLauncherGlobals.log is None)
	assert(WLauncherGlobals.config is None)
