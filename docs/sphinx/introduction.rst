
Introduction
======

Startup steps:

.. graphviz::

	digraph structs {
		node [shape=record];

		struct [label="wasp-launch starts"];
		struct0 [label="0. Logger pre-setups"];
		struct1 [label="1. Configuration loads"];
		struct2 [label="2. Logger re-setups"];
		struct3 [label="3. Application broker starts"];
		struct4 [label="{
			4. Internal applications start |
			4.1. Application registry starts |
			<message_proxy> 4.2  Proxy message broker starts
		}"];
		struct4_2_1 [label="4.2.1 Management listener starts"];
		struct4_2_2 [label="4.2.2 Network-state broker starts"];
		struct4_2_2_1 [label="4.2.2.1 Available network-services discover"];
		struct5 [label="5. Configuration-defined applications start"];

		struct -> struct0;
		struct0 -> struct1;
		struct1 -> struct2;
		struct2 -> struct3;
		struct3 -> struct4;
		struct4 -> struct5;
		struct4:message_proxy -> struct4_2_1;
		struct4:message_proxy -> struct4_2_2;
		struct4_2_2 -> struct4_2_2_1;
	}


0. Logger pre-setups
1. Configuration loads
2. Logger re-setups
3. Application broker starts
4. Internal applications start
4.1. Application registry starts
4.2  Proxy message broker starts
4.2.1 Management listener starts
4.2.2 Network-state broker starts
4.2.2.1 Available network-services discover
5. Configuration-defined applications start
5.1. Dependency check
5.2. Start and notify network services about available applications

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
1. 'sane' - check application for sanity
