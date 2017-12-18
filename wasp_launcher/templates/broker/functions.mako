## wasp_launcher/templates/broker/functions.mako
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

<%def name="single_list_entry_output(list_entry)">\
${list_entry[0]}: ${list_entry[1]}\
</%def>

<%def name="list_output(*list_entries, output_fn=None)">\
<% output_fn = output_fn if output_fn is not None else single_list_entry_output %>\
% for entry in list_entries:
${output_fn(entry)}
% endfor
</%def>

<%def name="simple_table_formatter_row(row, cells_length, delimiter)">\
<%
left_border = '%s ' % delimiter
int_border = ' %s ' % delimiter
right_border = ' %s' % delimiter
delta = lambda x: ' ' * (cells_length[x] - len(row[x]))
%>\
${left_border}\
% for i in range(len(row)):
${row[i]}${delta(i)}\
% if i < (len(row) - 1):
${int_border}\
% endif
% endfor
${right_border}\
</%def>

<%def name="simple_table_formatter(headers, rows)">\
<%

delimiter = '*'

def row_cells_length(items):
	return [len(x) for x in items]

cells_length = row_cells_length(headers)
for row in rows:
	row_length = row_cells_length(row)

	shorter_row, longer_row = row_length, cells_length
	if len(shorter_row) > len(longer_row):
		shorter_row, longer_row = longer_row, shorter_row

	for i in range(len(shorter_row)):
		cells_length[i] = max(shorter_row[i], longer_row[i])

	for i in range(len(shorter_row), len(longer_row)):
		cells_length.append(longer_row[i])

cell_count = len(cells_length)

row_length = 0
if cell_count > 0:
	row_length = ((cell_count - 1) * 3) + 4
	for i in cells_length:
		row_length += i

row_separator = delimiter * row_length

%>\
% if cell_count > 0:
${row_separator}
${simple_table_formatter_row(headers, cells_length, delimiter)}
${row_separator}
% for row in rows:
${simple_table_formatter_row(row, cells_length, delimiter)}
% endfor
${row_separator}
% endif
</%def>

<%def name="table_output(headers, rows, table_formatter_fn=None)">\
<% table_formatter_fn = table_formatter_fn if table_formatter_fn is not None else simple_table_formatter %>\
${table_formatter_fn(headers, rows)}\
</%def>