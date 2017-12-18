## wasp_launcher/templates/broker/help/context_help.mako
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
<%
	kit_context = broker_adapter.kit_context()
	kits = broker_adapter.kits()
	kit_description = {
		'core': 'Context for commands that interact with important built-in applications.',
		'apps': 'Context for commands that interact with user-defined applications.'
	}
%> \
\
% if kit_context in kit_description.keys():
This is a '${kit_context}' context. ${kit_description[kit_context]} You are able to switch to next context:
% else:
This is a '${kit_context}' context. You are able to switch to next context:
% endif
\
% for kit in kits:
\
% if kit.alias() is not None:
	- ${kit.alias()} | ${kit.name()} - ${kit.description()}
% else:
	- ${kit.name()} - ${kit.description()}
% endif
\
% endfor
<%include file="mako::com.binblob.wasp-launcher.broker::help::general_tip.mako"/>