#    powerwake address handling utility functions
#    Copyright (C) 2024 Daniel Collins <solemnwarning@solemnwarning.net>
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, version 3 of the License.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.

import netifaces
import re

# Parses and normalises a MAC address into a string of 12 hex nibbles.
#
# Returns None if the provided MAC address did not match any of the known
# address formats.

def normalise_mac(mac):
	regexps = [
		re.compile(r"^([0-9a-f]{2})([0-9a-f]{2})([0-9a-f]{2})([0-9a-f]{2})([0-9a-f]{2})([0-9a-f]{2})$", re.I),
		re.compile(r"^([0-9a-f]{1,2}):([0-9a-f]{1,2}):([0-9a-f]{1,2}):([0-9a-f]{1,2}):([0-9a-f]{1,2}):([0-9a-f]{1,2})$", re.I),
		re.compile(r"^([0-9a-f]{1,2})\.([0-9a-f]{1,2})\.([0-9a-f]{1,2})\.([0-9a-f]{1,2})\.([0-9a-f]{1,2})\.([0-9a-f]{1,2})$", re.I),
		re.compile(r"^([0-9a-f]{1,2})-([0-9a-f]{1,2})-([0-9a-f]{1,2})-([0-9a-f]{1,2})-([0-9a-f]{1,2})-([0-9a-f]{1,2})$", re.I),
	]
	
	for r in regexps:
		m = r.match(mac)
		
		if m != None:
			return "".join(list(map(lambda s: s.rjust(2, "0"), m.groups()))).lower()
	
	return None

# Get an array containing IPv4 addresses assigned to broadcast-capable network
# interfaces on the local system.
#
# Each element in the array is a dict in the following format:
#
# {
#     "ipaddr":    "192.168.0.1",
#     "netmask":   "255.255.255.0",
#     "broadcast": "192.168.0.255",
# }

def get_ipv4_broadcast_addresses():
	interfaces = netifaces.interfaces()
	addrs = []
	
	for i in interfaces:
		addresses = netifaces.ifaddresses(i)
		
		if netifaces.AF_INET in addresses:
			for ipv4 in addresses[netifaces.AF_INET]:
				if "broadcast" in ipv4:
					addrs.append({
						"ipaddr":    ipv4["addr"],
						"netmask":   ipv4["netmask"],
						"broadcast": ipv4["broadcast"],
					})
	
	return addrs
