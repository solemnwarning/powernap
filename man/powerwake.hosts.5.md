POWERWAKE.HOSTS 5 "OCTOBER 2024"
=======================================

NAME
----

powerwake.hosts - Powerwake host configuration database

DESCRIPTION
-----------

powerwake.hosts contains definitions of computers that can be started using
the `powerwake` program.

EXAMPLES
--------

    ; A machine that can be started using Wake-on-LAN.
    [host1.example.com]
    wol.mac = 01:23:45:67:89:AB

    ; A machine that can be started using Wake-on-LAN sent to a specific IP.
    [host2.example.com]
    wol.mac = 01:23:45:67:89:AB
    wol.host = wolproxy.example.com
    wol.port = 57749

    ; A machine that can be started using IPMI.
    [host3.example.com]
    ipmi.host = ipmi.host3.example.com
    ipmi.username = OPERATOR
    ipmi.password = 123456

FILES
-----

*/etc/powernap/powerwake.hosts*
  system-wide powerwake.hosts file.

*~/.config/powerwake.hosts*
  per-user powerwake.hosts file.

SEE ALSO
--------

powerwake(1)
