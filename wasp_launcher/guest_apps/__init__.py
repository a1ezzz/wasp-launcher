
from wasp_launcher.guest_apps.wasp import WWaspBasicApps
from wasp_launcher.guest_apps.debug import WWaspDebugApps


def __wasp_launcher_apps__():
	return [WWaspBasicApps, WWaspDebugApps]
