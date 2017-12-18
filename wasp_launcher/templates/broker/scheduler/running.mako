## wasp_launcher/templates/broker/scheduler/running.mako
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

tasks_count = 0
records = []

for instance, instance_name in running_tasks:
	if instance_name is None:
		instance_name = '<default instance>'

	running_records = instance.running_records()
	tasks_count += len(running_records)

	for running_record in running_records:
		scheduled_task = running_record.task()
		records.append([
			instance_name,
			scheduled_task.name(),
			running_record.task_uid(),
			na_formatter(scheduled_task.thread_name()),
			scheduled_task.brief_description()
		])
%>
Total tasks that is running at the moment: ${tasks_count}
${broker_functions.table_output(('Scheduler instance', 'Task name', 'Task uid', 'Thread', 'Task description'), records)}