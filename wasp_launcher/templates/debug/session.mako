
<%def name="debug_session_block(title_block, inner_block=None)">
	<DIV class="wasp_debug_session_block">
		<SPAN class="wasp_block_title">${title_block()}</SPAN>
		% if inner_block is not None:
			${inner_block()}
		% endif
	</DIV>
</%def>

<%def name="debug_session_details_block(title, context_obj, angular_trigger, details_block)">

	<%def name="title_block()">
		${title}
		% if context_obj is None:
			(Details unavailable due to data missing)
		% else:
			<SPAN class="wasp_details_trigger" data-ng-click="${angular_trigger} = !${angular_trigger}">
				<SPAN data-ng-if="${angular_trigger} != true">(Show details)</SPAN>
				<SPAN data-ng-if="${angular_trigger} == true">(Hide details)</SPAN>
			</SPAN>
		% endif
	</%def>

	<%def name="inner_block()">
		% if context_obj is not None:
			<DIV class="wasp_block_details" data-ng-if="${angular_trigger} == true">
				${details_block(context_obj)}
			</DIV>
		% endif
	</%def>

	${debug_session_block(title_block, inner_block)}
</%def>

<%def name="debug_session_intro_block()">
	<%def name="title_block()">
		Session start date: ${session['datetime'].strftime('%Y-%h-%d %H:%M:%S')}
	</%def>

	${debug_session_block(title_block)}
</%def>

<%def name="debug_session_request_block()">
	<%def name="details_block(item)">
		<DIV>Protocol: ${item['protocol'] | h} (HTTP/${item['protocol_version'] | h})</DIV>

		<DIV>Headers:<BR>
		% for header in item['headers']:
			${header[0] | h}: ${header[1] | h}<BR>
		% endfor
		</DIV>
	</%def>

	${debug_session_details_block(
		'Request: %s &quot;%s&quot;' % (request['method'], request['path']),
		request,
		'request_details',
		details_block
	)}
</%def>

<%def name="debug_session_route_block()">

	<%def name="details_block(item)">
		<DIV>Route HTTP methods: ${', '.join(item['route_methods'])}</DIV>
		<DIV>Route HTTP protocols: ${', '.join(item['route_protocols'])}</DIV>
		<DIV>Virtual hosts: ${item['route_virtual_hosts']}</DIV>
		<DIV>Server ports: ${item['route_ports']}</DIV>
		<DIV>Route arguments: ${item['route_args']}</DIV>
		<DIV>Presenter: &quot;${item['presenter_name']}&quot;</DIV>
		<DIV>Presenter action: &quot;${item['presenter_action']}&quot;</DIV>
		<DIV>Presenter arguments: ${item['presenter_args']}</DIV>
		<DIV>Original pattern: ${item['route_original_pattern']}</DIV>
	</%def>

	<%def name="no_route_title_block()">
		Route wasn't found
	</%def>

	% if target_route is not None:
		${debug_session_details_block(
			'Selected route: &quot;%s&quot;' % target_route['route_pattern'],
			target_route,
			'route_details',
			details_block
		)}
	% else:
		${debug_session_block(no_route_title_block)}
	% endif
</%def>

<%def name="debug_session_response_block()">

	<%def name="details_block(item)">
		<DIV>Headers: ${item['headers'] | h}</DIV>
		<DIV>Payload: ${item['data'] | h}</DIV>
	</%def>

	<%def name="no_response_title_block()">
		Response wasn't generated
	</%def>

	% if response is not None:
		${debug_session_details_block(
			'Response: %s' % response['status'],
			response,
			'response_details',
			details_block
		)}
	% else:
		${debug_session_block(no_response_title_block)}
	% endif
</%def>

<%def name="debug_session_exceptions_block()">

	<%def name="details_block(item)">

		<%def name="exceptions_details_block(exception_item)">
			<DIV>
				% for line in wasp_exceptions[i]['traceback'].split('\n'):
				<BR> ${line}
				% endfor
			</DIV>
		</%def>

		% for i in range(len(item)):
			${debug_session_details_block(
				'Exception: "%s"' % item[i]['exception'],
				item[i],
				'exceptions_details[%i]' % i,
				exceptions_details_block
			)}
		% endfor
	</%def>

	<%def name="no_exceptions_title_block()">
		No exception was raised
	</%def>

	% if len(wasp_exceptions) > 0:
		${debug_session_details_block(
			'Total exceptions: %i' % len(wasp_exceptions),
			wasp_exceptions,
			'exceptions_global_details',
			details_block
		)}
	% else:
		${debug_session_block(no_exceptions_title_block)}
	% endif
</%def>


<HTML data-ng-app="wasp-launcher::wasp-debug">
<HEAD>
	<LINK rel="stylesheet" type="text/css" href="/static.wasp-basic.bootstrap/latest/css/bootstrap.css">
	<LINK rel="stylesheet" type="text/css" href="/static.wasp-debug.debug/css/main.css">
	<SCRIPT type="text/javascript" src="/static.wasp-basic.angular/latest/angular.js"></SCRIPT>
	<SCRIPT type="text/javascript" src="/static.wasp-debug.debug/js/debug-angular.js"></SCRIPT>
</HEAD>
<BODY>
	<DIV data-ng-controller="wasp-launcher::wasp-debug::debug-controller">
		${debug_session_intro_block()}
		${debug_session_request_block()}
		${debug_session_route_block()}
		${debug_session_response_block()}
		${debug_session_exceptions_block()}
	</DIV>
</BODY>
</HTML>
