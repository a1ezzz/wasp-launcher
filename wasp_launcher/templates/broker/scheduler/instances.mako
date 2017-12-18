## wasp_launcher/templates/broker/scheduler/instances.mako
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
from wasp_general.cli.formatter import na_formatter

records = []

default_instance = scheduler.instance()
running, postponed = default_instance.records_status()
records.append([
	'<default instance>',
	str(running),
	str(default_instance.maximum_running_records()),
	str(postponed),
	na_formatter(default_instance.maximum_postponed_records())
])

named_instances = scheduler.named_instances()
for instance_name in named_instances:
	instance = scheduler.instance(instance_name)
	running, postponed = instance.records_status()
	records.append([
		instance_name,
		str(running),
		str(instance.maximum_running_records()),
		str(postponed),
		na_formatter(instance.maximum_postponed_records())
	])

%>
Total sources count: ${len(named_instances) + 1}
${broker_functions.table_output(('Scheduler instance name', 'Running tasks', 'Maximum running tasks',
'Postponed tasks', 'Maximum postponed tasks'), records)}