# -*- coding: utf-8 -*-
# wasp_launcher/beacon.py
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

# TODO: document the code
# TODO: write tests for the code

# noinspection PyUnresolvedReferences
from wasp_launcher.version import __author__, __version__, __credits__, __license__, __copyright__, __email__
# noinspection PyUnresolvedReferences
from wasp_launcher.version import __status__

from wasp_general.verify import verify_type
from wasp_general.config import WConfig

from wasp_general.network.primitives import WIPV4SocketInfo
from wasp_general.network.beacon.beacon import WNetworkBeacon, WNetworkBeaconCallback
from wasp_general.network.beacon.transport import WBroadcastBeaconTransport
from wasp_general.network.beacon.messenger import WHostgroupBeaconMessenger
from wasp_launcher.globals import WLauncherGlobals


class WLauncherBeaconMessenger(WHostgroupBeaconMessenger):
	""" Messenger that works on server, client and neighbor finder sides
	"""

	__hello_message__ = b'WLauncherBeacon'

	@verify_type(neighbor_finder=bool)
	def __init__(self, neighbor_finder=False):
		hostgroups = WLauncherGlobals.config.split_option('wasp-launcher::discovery::beacon', 'hostgroups')
		WHostgroupBeaconMessenger.__init__(
			self, WLauncherBeaconMessenger.__hello_message__, *hostgroups, invert_hello=True
		)
		self.__neighbor_finder = neighbor_finder

	@verify_type(beacon_config=WConfig, invert_hello=bool)
	def _message(self, beacon_config, invert_hello=False):
		config = WConfig()
		config.merge(beacon_config)
		if self.__neighbor_finder is True:
			config['wasp-general::network::beacon']['public_address'] = config['wasp-general::network::beacon']['address']
		return WHostgroupBeaconMessenger._message(self, config, invert_hello=invert_hello)


class WLauncherBeaconServer(WNetworkBeacon):
	""" Network server beacon
	"""

	class WBeaconCallback(WNetworkBeaconCallback):
		@verify_type(message=bytes, source=WIPV4SocketInfo, description=WNetworkBeaconCallback.WDataDescription)
		def __call__(self, message, source, description):
			pass

	def __init__(self):
		WNetworkBeacon.__init__(
			self, server_mode=True, config=WLauncherGlobals.config,
			config_section='wasp-launcher::discovery::beacon', messenger=WLauncherBeaconMessenger(),
			transport=WBroadcastBeaconTransport(),
			callback=WLauncherBeaconServer.WBeaconCallback(), server_receives=True
		)


class WLauncherBeaconClient(WNetworkBeacon):
	""" Network beacon client, that can work as neighbor finder
	"""

	class WBeaconCallback(WNetworkBeaconCallback):
		@verify_type(message=bytes, source=WIPV4SocketInfo, description=WNetworkBeaconCallback.WDataDescription)
		def __call__(self, message, source, description):
			pass

	@verify_type(neighbor_finder=bool)
	def __init__(self, neighbor_finder=False):
		WNetworkBeacon.__init__(
			self, server_mode=False, config=WLauncherGlobals.config,
			config_section='wasp-launcher::discovery::beacon',
			messenger=WLauncherBeaconMessenger(neighbor_finder=neighbor_finder),
			transport=WBroadcastBeaconTransport(), callback=WLauncherBeaconClient.WBeaconCallback(),
			server_receives=False
		)
