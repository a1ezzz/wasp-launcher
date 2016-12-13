# -*- coding: utf-8 -*-

import pytest
import os

from wasp_general.config import WConfig

from wasp_launcher.config import WLauncherConfig
from wasp_launcher.launcher_registry import WLauncherTask
from wasp_launcher.globals import WLauncherGlobals


@pytest.fixture
def fin_config(request):
	def fin():
		WLauncherGlobals.config = None
		del os.environ[WLauncherConfig.__environment_var__]
	request.addfinalizer(fin)


@pytest.fixture
def temp_files(request):
	from conftest import temp_file
	return (temp_file(request), temp_file(request))


class TestWLauncherConfig:

	@pytest.mark.usefixtures('global_log', 'fin_config')
	def test_task(self, temp_files):
		tempfile1, tempfile2 = temp_files
		assert(isinstance(WLauncherConfig(), WLauncherTask) is True)

		with open(tempfile1, 'w') as f1:
			f1.write('''
				[section1]
				option1 = 1
				option2 = 2
			''')

		with open(tempfile2, 'w') as f2:
			f2.write('''
				[section1]
				option2 = bar

				[section2]
				option = foo
			''')

		class Config(WLauncherConfig):

			__configuration_default__ = tempfile1
			__registry_tag__ = WLauncherConfig.__registry_tag__ + '_test'

		os.environ[WLauncherConfig.__environment_var__] = tempfile2

		task = Config.start_dependent_task()
		assert(isinstance(WLauncherGlobals.config, WConfig) is True)
		assert(WLauncherGlobals.config['section1']['option1'] == '1')
		assert(WLauncherGlobals.config['section1']['option2'] == 'bar')
		assert(WLauncherGlobals.config['section2']['option'] == 'foo')

		task.stop()
		assert(WLauncherGlobals.config is None)

		os.unlink(tempfile1)
		os.unlink(tempfile2)
		pytest.raises(RuntimeError, Config.start_dependent_task)
