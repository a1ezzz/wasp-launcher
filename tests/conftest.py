
from tempfile import mktemp
import os
import pytest
import logging

from wasp_launcher.core import WAppsGlobals


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
	WAppsGlobals.log = logging.getLogger('wasp-launcher-pytest')

	def fin():
		WAppsGlobals.log = None
	request.addfinalizer(fin)
