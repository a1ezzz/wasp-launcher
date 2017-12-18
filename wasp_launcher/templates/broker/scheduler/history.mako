## wasp_launcher/templates/broker/scheduler/history.mako
##
## Copyright (C) 2017 the wasp-launcher authors and contributors
## <see AUTHORS file>
##
## This file is part of wasp-launcher.
##
## Wasp-launcher is free software: you can redistribute it and/or modify
## it under the terms of the GNU Lesser General Public License as published by
## the Free Software Foundation, either version 3 of the License, or
## (at your option) any later version.
##
## Wasp-launcher is distributed in the hope that it will be useful,
## but WITHOUT ANY WARRANTY; without even the implied warranty of
## MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
## GNU Lesser General Public License for more details.
##
## You should have received a copy of the GNU Lesser General Public License
## along with wasp-launcher.  If not, see <http://www.gnu.org/licenses/>.
<%namespace name="broker_functions" file="mako::com.binblob.wasp-launcher.broker::functions.mako"/>\
<%
from wasp_general.task.thread_tracker import WTrackerEvents
from wasp_general.cli.formatter import local_datetime_formatter

records = []

for record in history_records:
	if record.record_type == WTrackerEvents.start:
		status = 'Started'
	elif record.record_type == WTrackerEvents.stop:
		status = 'Stopped'
	elif record.record_type == WTrackerEvents.termination:
		status = 'Terminated'
	elif record.record_type == WTrackerEvents.exception:
		status = 'Exception raised'
	elif record.record_type == WTrackerEvents.wait:
		status = 'Waited'
	elif record.record_type == WTrackerEvents.drop:
		status = 'Dropped'
	else:
		# unknow type
		continue

	records.append([
		record.thread_task.name(),
		record.thread_task.uid(),
		status,
		local_datetime_formatter(record.registered_at),
		record.thread_task.brief_description()
	])
%>
Records stored: ${len(records)}
${broker_functions.table_output(('Task name', 'Task uid', 'Status', 'Event time', 'Task description'), records)}