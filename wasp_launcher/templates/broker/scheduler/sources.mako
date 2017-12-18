## wasp_launcher/templates/broker/scheduler/sources.mako
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
from wasp_general.cli.formatter import na_formatter, local_datetime_formatter

sources_count = 0
records = []

for instance, instance_name in scheduler:
	if instance_name is None:
		instance_name = '<default instance>'

	task_sources = instance.task_sources()
	for source in task_sources:
		records.append([
			instance_name,
			source.name(),
			na_formatter(source.description()),
			str(source.tasks_planned()),
			na_formatter(source.next_start(), local_datetime_formatter)
		])

	sources_count += len(task_sources)
%>
Total sources count: ${sources_count}
${broker_functions.table_output(
	('Scheduler instance', 'Source name', 'Source description', 'Scheduled tasks', 'Next scheduled task'), records
)}