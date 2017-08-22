#!/usr/bin/python3
# -*- coding: utf-8 -*-
# wasp-launcher-cli.py
#
# Copyright (C) 2016 the wasp-launcher authors and contributors
# <see AUTHORS file>
#
# This file is part of wasp-launcher.
#
# Wasp-launcher is free software: you can redistribute it and/or modify
# it under the terms of the GNU Lesser General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Wasp-launcher is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Lesser General Public License for more details.
#
# You should have received a copy of the GNU Lesser General Public License
# along with wasp-launcher.  If not, see <http://www.gnu.org/licenses/>.

# noinspection PyUnresolvedReferences
from wasp_launcher.version import __author__, __version__, __credits__, __license__, __copyright__, __email__
# noinspection PyUnresolvedReferences
from wasp_launcher.version import __status__

import os
import signal

from wasp_launcher.apps import WHostAppRegistry, WAppsGlobals
# noinspection PyUnresolvedReferences
import wasp_launcher.host_apps
from wasp_launcher.broker_cli import WBrokerCLI


if __name__ == '__main__':
	print('CLI is starting')

	config_task = 'com.binblob.wasp-launcher.host-app.config'
	WHostAppRegistry.start_task(config_task)

	os.environ['TERM'] = 'linux'  # TODO: remove magic value!

	if WAppsGlobals.config.getboolean('wasp-launcher::broker::connection::cli', 'named_socket') is True:
		named_socket = WAppsGlobals.config['wasp-launcher::broker::connection']['named_socket_path'].strip()
		connection = connection = 'ipc://%s' %  named_socket
	else:
		tcp_address = WAppsGlobals.config['wasp-launcher::broker::connection::cli']['tcp_address'].strip()
		if len(tcp_address) > 0:
			if ':' not in tcp_address:
				tcp_port = WAppsGlobals.config.getint('wasp-launcher::broker::connection', 'port')
				tcp_address += (':%i' % tcp_port)
			connection = 'tcp://%s' % tcp_address
		else:
			raise RuntimeError('At least one CLI connection option must be specified in configuration')

	cli = WBrokerCLI(connection)

	def shutdown_signal(signum, frame):
		cli.stop()
		WHostAppRegistry.stop_task(config_task, stop_requirements=True)

	signal.signal(signal.SIGTERM, shutdown_signal)
	signal.signal(signal.SIGINT, shutdown_signal)

	cli.start()

# any-context:
# -- exit
# -- quit
# -- help
# -- ..
# -- .
# host-app context:
# host-app [full qualified application name|application alias] <commands>
# like:
# <for com.binblob.wasp-launcher.host-app.command::core - core>
# -- host-app core threads
# like:
# <for com.binblob.wasp-launcher.host-app.command::model-db - model-db>
# -- host-app model-db deploy
# -- host-app model-db deploy scheme
# -- host-app model-db deploy data
# -- host-app model-db deploy uninstall
# -- host-app model-db deploy uninstall
# <for com.binblob.wasp-launcher.host-app.command::model-obj - model-obj>
# -- host-app model-obj [model-cls] list <query args>
# -- host-app model-obj [model-cls] list-verbose <query args>
# -- host-app model-obj [model-cls] create <create args>
# -- host-app model-obj [model-cls] delete <query args>
# -- host-app model-obj [model-cls] update <query args>
# -- host model-obj [model-cls] exec <query args> [method name] <method args>
# <for com.binblob.wasp-launcher.host-app.command::guest - guest>
# -- host-app guest list
# -- host-app guest model list
# -- host-app guest presenter list
# -- host-app guest schedule list
# -- host-app guest [guest-app] model list
# -- host-app guest [guest-app] presenter list
# -- host-app guest [guest-app] schedule list
# <for com.binblob.wasp-launcher.host-app.command::schedule - schedule>
# -- host-app schedule
# guest-app context:
# guest-app [full qualified application name|application alias] <commands>
