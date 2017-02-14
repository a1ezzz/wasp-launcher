
from wasp_launcher.apps.wasp import WWaspBasicApps
from wasp_launcher.apps.debug import WWaspDebugApps


def __wasp_launcher_apps__():
	return [WWaspBasicApps, WWaspDebugApps]
