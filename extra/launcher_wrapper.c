/* extra/launcher_wrapper.c
*
* Copyright (C) 2017 the wasp-launcher authors and contributors
* <see AUTHORS file>
*
* This file is part of wasp-launcher.
*
* Wasp-launcher is free software: you can redistribute it and/or modify
* it under the terms of the GNU Lesser General Public License as published by
* the Free Software Foundation, either version 3 of the License, or
* (at your option) any later version.
*
* Wasp-launcher is distributed in the hope that it will be useful,
* but WITHOUT ANY WARRANTY; without even the implied warranty of
* MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
* GNU Lesser General Public License for more details.
*
* You should have received a copy of the GNU Lesser General Public License
* along with wasp-launcher.  If not, see <http://www.gnu.org/licenses/>.
*/


#include <unistd.h>
#include <stdio.h>
#include <sys/capability.h>
#include <sys/prctl.h>

#ifndef PYTHON_INTERP
#error PYTHON_INTERP must be defined
#endif

#ifndef LAUNCHER_SCRIPT
#error LAUNCHER_SCRIPT must be defined
#endif

int main(int argc, char* argv[])
{
	cap_t caps = cap_get_proc ();
	cap_value_t newcaps[1] = { CAP_NET_BIND_SERVICE, };
	cap_set_flag (caps, CAP_INHERITABLE, 1, newcaps, CAP_SET);
	if (cap_set_proc (caps) != 0){
		printf("Warning - unable to set \"CAP_NET_BIND_SERVICE\" capability properly\n");
	}
	if (prctl(PR_CAP_AMBIENT, PR_CAP_AMBIENT_RAISE, CAP_NET_BIND_SERVICE, 0, 0, 0) != 0){
		printf("Warning - unable to set ambient capability properly\n");
	}

	printf("Wrapper is ready to start launcher\n");

	execl(PYTHON_INTERP, PYTHON_INTERP, LAUNCHER_SCRIPT, NULL);
	return 0;
}
