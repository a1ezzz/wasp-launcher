
from tempfile import mktemp
import os
import pytest
import logging

from wasp_launcher.globals import WLauncherGlobals


@pytest.fixture
def temp_file(request):
	filename = mktemp('pytest-wasp-launcher-')

	def fin():
		if os.path.exists(filename):
			os.unlink(filename)
	request.addfinalizer(fin)
	return filename


@pytest.fixture
def global_log(request):
	WLauncherGlobals.log = logging.getLogger('wasp-launcher-pytest')

	def fin():
		WLauncherGlobals.log = None
	request.addfinalizer(fin)
