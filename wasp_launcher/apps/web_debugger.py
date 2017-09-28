# -*- coding: utf-8 -*-
# wasp_launcher/apps/web_debugger.py
#
# Copyright (C) 2016-2017 the wasp-launcher authors and contributors
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

import traceback
from uuid import uuid4

from wasp_general.verify import verify_type
from wasp_general.datetime import utc_datetime
from wasp_general.network.web.debug import WWebDebugInfo
from wasp_general.network.web.proto import WWebRequestProto, WWebResponseProto
from wasp_general.network.web.service import WWebTargetRoute
from wasp_general.network.web.headers import WHTTPHeaders

from wasp_launcher.core import WSyncApp, WAppsGlobals
from wasp_launcher.mongodb import WMongoConnection


class WWebAppDebugger(WWebDebugInfo):

	class DebugSession:

		def __init__(self):
			self.uuid = uuid4()
			self.datetime = utc_datetime()

	def __init__(self):
		WWebDebugInfo.__init__(self)

		self.__sessions = {}

		self.mode = WAppsGlobals.config["wasp-launcher::web:debug"]["mode"].lower()
		if self.mode not in ['on', 'off', 'on error']:
			self.mode = 'off'

	def session_id(self):
		if self.mode != 'off':
			session = WWebAppDebugger.DebugSession()
			self.__sessions[session.uuid] = {
				'session': session
			}
			return session

	def save_session_id(self, session_id):
		if session_id.uuid not in self.__sessions:
			return

		session_data = self.__sessions[session_id.uuid]
		if 'session' not in session_data:
			return

		session_id = session_data['session']
		WWebAppDebuggerDatastore.__mongo_sessions__.insert_one({
			'uuid': session_id.uuid,
			'datetime': session_id.datetime
		})

	@verify_type(request=WWebRequestProto, protocol_version=str, protocol=str)
	def request(self, session_id, request, protocol_version, protocol):
		request.__wlauncher_debugger_session__ = session_id
		if self.mode != 'off':
			self.__sessions[session_id.uuid]['request'] = request
			self.__sessions[session_id.uuid]['protocol_version'] = protocol_version
			self.__sessions[session_id.uuid]['protocol'] = protocol

	def save_request(self, session_id):
		if session_id.uuid not in self.__sessions:
			return

		session_data = self.__sessions[session_id.uuid]
		if 'request' not in session_data:
			return
		if 'protocol_version' not in session_data:
			return
		if 'protocol' not in session_data:
			return

		request = session_data['request']
		protocol_version = session_data['protocol_version']
		protocol = session_data['protocol']

		WWebAppDebuggerDatastore.__mongo_requests__.insert_one({
			'uuid': session_id.uuid,
			'protocol': protocol,
			'protocol_version': protocol_version,
			'method': request.method(),
			'path': request.path(),
			'headers': self.headers(request.headers()),
			'data': request.request_data()
		})

	@verify_type(response=WWebResponseProto)
	def response(self, session_id, response):
		if self.mode != 'off':
			self.__sessions[session_id.uuid]['response'] = response

	def save_response(self, session_id):
		if session_id.uuid not in self.__sessions:
			return

		session_data = self.__sessions[session_id.uuid]
		if 'response' not in session_data:
			return

		response = session_data['response']
		WWebAppDebuggerDatastore.__mongo_responses__.insert_one({
			'uuid': session_id.uuid,
			'status': response.status(),
			'headers': self.headers(response.headers()),
			'data': response.response_data()
		})

	@verify_type(target_route=(WWebTargetRoute, None))
	def target_route(self, session_id, target_route):
		if self.mode != 'off':
			self.__sessions[session_id.uuid]['target_route'] = target_route

	def save_target_route(self, session_id):
		if session_id.uuid not in self.__sessions:
			return

		session_data = self.__sessions[session_id.uuid]
		if 'target_route' not in session_data:
			return

		target_route = session_data['target_route']
		if target_route is None:
			return

		WWebAppDebuggerDatastore.__mongo_target_routes__.insert_one({
			'uuid': session_id.uuid,
			'presenter_name': target_route.presenter_name(),
			'presenter_action': target_route.presenter_action(),
			'presenter_args': target_route.presenter_args(),

			'route_original_pattern': target_route.route().original_pattern,
			'route_pattern': target_route.route().pattern,
			'route_args': target_route.route().route_args,
			'route_virtual_hosts': target_route.route().virtual_hosts,
			'route_ports': target_route.route().ports,
			'route_protocols': target_route.route().protocols,
			'route_methods': target_route.route().methods
		})

	@verify_type(exc=Exception)
	def exception(self, session_id, exc):
		if self.mode != 'off':
			if 'exception_data' not in self.__sessions[session_id.uuid]:
				self.__sessions[session_id.uuid]['exception_data'] = []

			self.__sessions[session_id.uuid]['exception_data'].append(
				{'exception': exc, 'traceback': traceback.format_exc()}
			)

	def save_exception(self, session_id):
		if session_id.uuid not in self.__sessions:
			return

		session_data = self.__sessions[session_id.uuid]
		if 'exception_data' not in session_data:
			return

		# TODO: replace with __mongo_exceptions__.insert_many

		for exception_data in session_data['exception_data']:
			exc = exception_data['exception']
			traceback_data = exception_data['traceback']

			WWebAppDebuggerDatastore.__mongo_exceptions__.insert_one({
				'uuid': session_id.uuid,
				'exception': str(exc),
				'traceback': traceback_data
			})

	def finalize(self, session_id):
		if self.mode == 'off':
			return

		if self.mode == 'on error':
			if 'exception_data' not in self.__sessions[session_id.uuid]:
				status = self.__sessions[session_id.uuid]['response'].status()
				if status is None or status == 200:
					return

		try:
			self.save_session_id(session_id)
		except Exception as e:
			self.exception(session_id, e)

		try:
			self.save_request(session_id)
		except Exception as e:
			self.exception(session_id, e)

		try:
			self.save_response(session_id)
		except Exception as e:
			self.exception(session_id, e)

		try:
			self.save_target_route(session_id)
		except Exception as e:
			self.exception(session_id, e)

		self.save_exception(session_id)
		self.__sessions.pop(session_id.uuid)

	@verify_type(headers=WHTTPHeaders)
	def headers(self, headers):
		result = []
		for header_name in headers.headers():
			for header_value in headers[header_name]:
				result.append((header_name, header_value))
		return result


class WWebAppDebuggerDatastore(WSyncApp):
	""" Task that creates connection to a mongodb server
	"""

	__registry_tag__ = 'com.binblob.wasp-launcher.apps.web-debugger::datastore'
	""" Task tag
	"""

	__dependency__ = [
		'com.binblob.wasp-launcher.apps.config'
	]

	__mongo_connection__ = None

	__mongo_sessions__ = None
	__mongo_requests__ = None
	__mongo_responses__ = None
	__mongo_target_routes__ = None
	__mongo_exceptions__ = None

	def start(self):
		if WWebAppDebuggerDatastore.__mongo_connection__ is None:
			WWebAppDebuggerDatastore.__mongo_connection__ = WMongoConnection.create(
				'wasp-launcher::web:debug', 'mongo_connection', 'mongo_database'
			)

		WWebAppDebuggerDatastore.__mongo_sessions__ = WWebAppDebuggerDatastore.__mongo_connection__['sessions']
		WWebAppDebuggerDatastore.__mongo_requests__ = WWebAppDebuggerDatastore.__mongo_connection__['requests']
		WWebAppDebuggerDatastore.__mongo_responses__ = \
			WWebAppDebuggerDatastore.__mongo_connection__['responses']
		WWebAppDebuggerDatastore.__mongo_target_routes__ = \
			WWebAppDebuggerDatastore.__mongo_connection__['target_routes']
		WWebAppDebuggerDatastore.__mongo_exceptions__ = \
			WWebAppDebuggerDatastore.__mongo_connection__['exceptions']

		WAppsGlobals.log.info('Web-debugger datastore started')

	def stop(self):
		if WWebAppDebuggerDatastore.__mongo_connection__ is not None:
			WWebAppDebuggerDatastore.__mongo_connection__.close()

		WWebAppDebuggerDatastore.__mongo_sessions__ = None
		WWebAppDebuggerDatastore.__mongo_requests__ = None
		WWebAppDebuggerDatastore.__mongo_responses__ = None
		WWebAppDebuggerDatastore.__mongo_target_routes__ = None
		WWebAppDebuggerDatastore.__mongo_exceptions__ = None

		WWebAppDebuggerDatastore.__mongo_connection__ = None

		WAppsGlobals.log.info('Web-debugger stopped')
