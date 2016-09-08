
Introduction
======

Startup steps:

.. graphviz::

	digraph structs {
		node [shape=record];

		struct [label="wasp-launch starts"];
		struct0 [label="0. Logger sets up"];
		struct1 [label="1. Configuration loads"];
		struct2 [label="2. Application broker starts"];
		struct3 [label="{
			3. Internal applications start |
			3.1. Application registry starts |
			<message_proxy> 3.2  Proxy message broker starts
		}"];
		struct3_2_1 [label="3.2.1 Management listener starts"];
		struct3_2_2 [label="3.2.2 Network-state broker starts"];
		struct3_2_2_1 [label="3.2.2.1 Available network-services discover"];
		struct4 [label="4. Configuration-defined applications start"];

		struct -> struct0;
		struct0 -> struct1;
		struct1 -> struct2;
		struct2 -> struct3;
		struct3 -> struct4;
		struct3:message_proxy -> struct3_2_1;
		struct3:message_proxy -> struct3_2_2;
		struct3_2_2 -> struct3_2_2_1;
	}


0. Logger sets up
1. Configuration loads
2. Application broker starts
3. Internal applications start
3.1. Application registry starts
3.2  Proxy message broker starts
3.2.1 Management listener starts
3.2.2 Network-state broker starts
3.2.2.1 Available network-services discover
4. Configuration-defined applications start
4.1. Dependency check
4.2. Start and notify network services about available applications

Application types:
1. Threaded application (internal apps mostly)
2. Forked application
3. System-service application (sysvinit/openrc/systemd)

Threaded and forked applications has next entry points:
1. 'status' - check if application is running.
2. 'start'- run application
3. 'stop' - send signal to stop application
4. 'terminate' - terminate application

Optional entry points:
1. 'health' - check application for health
