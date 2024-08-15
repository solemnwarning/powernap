POWERWAKE 1 "AUGUST 2024"
=======================================

NAME
----

powerwake - smart utilty for remotely waking sleeping systems

SYNOPSIS
--------

Wake a machine using Wake-on-LAN:
  `powerwake` [-b *broadcast-ip*] [-p *broadcast-port*] [-w] *mac*|*ip*|*hostname*

Wake a machine using IPMI:
  `powerwake` -I -U *ipmi-username* -P *ipmi-password* *ipmi-ip-or-hostname*

Wake a machine using IPMI and wait for it to boot:
  `powerwake` -I -U *username* -P *password* -w -b *ip-or-hostname* *ipmi-ip-or-hostname*

DESCRIPTION
-----------

`powerwake` wakes a sleeping or powered off system using Wake-on-LAN or IPMI.

OPTIONS
-------

`-b|--broadcast` *ip*
  Sets the address to send WoL packets to

`-p|--port` *port*
  Sets the port to send WoL packets to

`-w|--wait`
  Wait for the target system to finish booting
  (requires `powernapd` to be configured on the target)

`-t|--timeout` *seconds*
  How long to wait for host to start up
  (only applicable when `--wait` is specified, defaults to 60)

`-I|--ipmi`
  Power on the system using IPMI

`-U|--ipmi-username` *username*
  Sets the username when using --ipmi

`-P|--ipmi-password` *password*
  Sets the password when using --ipmi

FILES
-----

*/etc/ethers*
  Ethernet address to IP number database, see ethers(5) for details.

*~/.config/powerwake.hosts*, */etc/powernap/powerwake.hosts*
  Powerwake host configuration database, see powerwake.hosts(5) for details.

CONFIGURATION IN DNS
--------------------

`powerwake` will attempt to find how to wake a host using DNS if a
hostname is provided on the command line.

**For Wake-on-LAN:**

; MAC address for host.example.com  
*host.example.com*  **TXT**  "**powerwake.wol.mac**=*aa:bb:cc:dd:ee:ff*"

; IP address and port to send WoL packets to (optional)  
*host.example.com*  **TXT**  "**powerwake.wol.host**=*wolproxy.example.com*"  
*host.example.com*  **TXT**  "**powerwake.wol.port**=*1234*"

**For IPMI:**

; IP address or hostname of the IPMI controller  
*host.example.com*  **TXT**  "**powerwake.ipmi.host**=*ipmi.host.example.com*"

; IPMI port number (defaults to 623)  
*host.example.com*  **TXT**  "**powerwake.ipmi.port**=*624*"

; IPMI credentials (may be provided on command line instead)  
*host.example.com*  **TXT**  "**powerwake.ipmi.username**=*OPERATOR*"  
*host.example.com*  **TXT**  "**powerwake.ipmi.password**=*insecure*"

AUTHOR
------

This manpage and the utility was written by Dustin Kirkland <kirkland@canonical.com> for Ubuntu systems (but may be used by others).  Permission is granted to copy, distribute and/or modify this document under the terms of the GNU General Public License, Version 3 published by the Free Software Foundation.

On Debian systems, the complete text of the GNU General Public License can be found in /usr/share/common-licenses/GPL.

SEE ALSO
--------

ethers(5), powerwake.hosts(5)
