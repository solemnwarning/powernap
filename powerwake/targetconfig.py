#    powerwake target configuration parsing/discovery
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

# This file contains functions for loading "target configs" from different
# sources (DNS, ethers file, etc).
#
# If successful, the returned config dictionary contains the following keys:
#
# "target"       The provided target hostname, IP or MAC address
# "target.ip"    The IP address of the target host (if known)
# "method"       "wol" or "ipmi"
#
# "wait"            Placeholder
# "wait.timeout"    Placeholder
# "wait.ip"         IP address to poll for readiness (optional)
# "wait.port"       Port number to poll powernapd on (optional)
#
# When "method" is "wol":
#
# "wol.mac"   MAC address of host to wake
# "wol.ip"    IP address to send WOL packets to (optional)
# "wol.port"  UDP port to send WOL packets to (optional)
#
# When "method" is "ipmi"
#
# "ipmi.host"        Hostname or IP address of BMC
# "ipmi.port"        IPMI port number
# "ipmi.username"    Username for BMC authentication (optional)
# "ipmi.password"    Password for BMC authentication (optional)

import configparser
import dns.exception
import dns.resolver
import re
import socket
import sys
import warnings

import powerwake.addressutils

class Error(Exception):
	def __init__(self, message):
		super().__init__(message)

# Parse the text from a TXT record into a name/value pair according to the
# rules in RFC 1464.
#
# Returns the name and value, or None and None in case the record is not a
# valid RFC 1464 name/value attribute pair.

def parse_rfc1464_attribute(text):
	# Split the record on the first '=' which isn't preceeded by a '`'
	words = re.split(r"(?<!`)=", text, 1)
	
	if len(words) == 2:
		[ name, value ] = words
		
		# Remove leading/trailing whitespace from the attribute name
		name = re.sub(r"^\s*", "", name)
		name = re.sub(r"((?<!`)\s)*$", "", name)
		
		# Remove any '`' characters used to escape a character in the attribute name
		name = re.sub(r"`(.)", r"\g<1>", name)
		
		# Empty attribute names are not allowed
		if name == "":
			return None, None
		
		return name, value
		
	else:
		return None, None

# Parses a dnspython dns.resolver.Answer object and returns a dictionary of all
# RFC 1464 attribute pairs in the response.

def parse_rfc1464_result(answer):
	attributes = {}
	
	for a in answer:
		# TODO: Check if 'a' is actually a TXT record?
		
		for bs in a.strings:
			s = bs.decode('ascii')
			name, value = parse_rfc1464_attribute(s)
			
			if name != None:
				attributes[name] = value
	
	return attributes

def parse_dns_result(hostname, a_address, attributes):
	config = {}
	config["method"] = None
	config["wait"] = False
	
	config["target"] = hostname
	
	if a_address != None:
		config["target.ip"] = a_address
	
	def set_method(method):
		if config["method"] != None and config["method"] != method:
			other_method = config["method"]
			raise Error(f"{hostname} has attributes for multiple methods ({other_method}, {method})")
		
		config["method"] = method
	
	for attr_name, attr_value in attributes.items():
		if not attr_name.startswith("powerwake."):
			continue
		
		def attr_host_to_ip():
			try:
				return socket.gethostbyname(attr_value)
				
			except Exception as e:
				raise Error(f"{hostname} {attr_name} attribute cannot be resolved: " + str(e))
		
		def attr_port_number():
			try:
				port = int(attr_value)
				
				if port < 0 or port > 65535:
					raise ValueError(f"port number {port} is out of range")
				
				return port
				
			except ValueError:
				raise Error(f"{hostname} {attr_name} attribute has invalid port number")
		
		if attr_name == "powerwake.wol.mac":
			set_method("wol")
			
			mac = powerwake.addressutils.normalise_mac(attributes["powerwake.wol.mac"])
			if mac == None:
				raise Error(f"{hostname} powerwake.wol.mac attribute in DNS has invalid format")
			
			config["wol.mac"] = mac
			
		elif attr_name == "powerwake.wol.host":
			set_method("wol")
			config["wol.ip"] = attr_host_to_ip()
			
		elif attr_name == "powerwake.wol.port":
			set_method("wol")
			config["wol.port"] = attr_port_number()
			
		elif attr_name == "powerwake.ipmi.host":
			set_method("ipmi")
			config["ipmi.host"] = attr_value
			
		elif attr_name == "powerwake.ipmi.port":
			set_method("ipmi")
			config["ipmi.port"] = attr_port_number()
			
		elif attr_name == "powerwake.ipmi.username":
			set_method("ipmi")
			config["ipmi.username"] = attr_value
			
		elif attr_name == "powerwake.ipmi.password":
			set_method("ipmi")
			config["ipmi.password"] = attr_value
			
		else:
			print(f"Ignoring unknown {hostname} attribute {attr_name}")
	
	if config["method"] == "wol":
		if not "wol.mac" in config:
			raise Error(f"{hostname} powerwake.wol.mac attribute is not present in DNS")
	
	elif config["method"] == "ipmi":
		if not "ipmi.host" in config:
			raise Error(f"{hostname} powerwake.ipmi.host attribute is not present in DNS")
	
	if config["method"] != None:
		return config
	else:
		return None

# Search DNS for a valid and complete powerwake target configuration for the
# given hostname.
#
# Returns a dictionary if a valid configuration was found, None if none was
# found and throws a Error exception if a malformed configuration was
# found.

def target_config_from_dns(hostname):
	a_address = None
	txt = None
	
	try:
		a = dns.resolver.resolve(hostname, "A")
		
		if a != None and len(a) == 1:
			a_address = a[0].address
	
	except dns.exception.DNSException:
		# No A record found, not necessarily an error.
		pass
	
	try:
		txt = dns.resolver.resolve(hostname, "TXT")
	
	except dns.exception.DNSException:
		# No TXT record found, no powerwake config here.
		return None
	
	attributes = parse_rfc1464_result(txt)
	
	return parse_dns_result(hostname, a_address, attributes)

# Search an /etc/ethers format file for the given target and return a target
# config to wake it via WOL if found.

def target_config_from_ethers(target, filename, gethostbyname = socket.gethostbyname):
	target_ip = None
	try:
		target_ip = gethostbyname(target)
	except:
		pass
	
	target_mac = powerwake.addressutils.normalise_mac(target)
	
	comment_re = re.compile(r"^\s*#")
	empty_re = re.compile(r"^\s*$")
	pair_re = re.compile(r"^([0-9a-f]{1,2}(?::[0-9a-f]{1,2}){5})\s+(\S+)$", re.I)
	
	config = None
	
	f = open(filename, 'r')
	for i in f.readlines():
		if comment_re.match(i) or empty_re.match(i):
			# Empty line or comment
			continue
		
		if match := pair_re.match(i):
			mac = powerwake.addressutils.normalise_mac(match.group(1))
			
			if mac == None:
				# Malformed MAC address
				continue
			
			ipaddr_or_hostname = match.group(2)
			ipaddr = None
			
			try:
				ipaddr = gethostbyname(ipaddr_or_hostname)
			except:
				pass
			
			if mac == target_mac:
				config = {
					"target": target,
					"method": "wol",
					"wait": False,
					"wol.mac": mac,
				}
				
				if ipaddr != None:
					config["target.ip"] = ipaddr
				
				break
			
			if ipaddr_or_hostname == target or (ipaddr != None and ipaddr == target_ip):
				config = {
					"target": target,
					"method": "wol",
					"wait": False,
					"wol.mac": mac,
				}
				
				if target_ip != None:
					config["target.ip"] = target_ip
				
				break
		else:
			# Malformed line
			warnings.warn(f"Unexpected data at {filename} line {line_num}", RuntimeWarning)
			break
		
	f.close()
	
	return config

def target_config_from_hosts_section(filename, gethostbyname, cfg, section_name):
	config = {}
	config["method"] = None
	config["wait"] = False
	
	config["target"] = section_name
	
	target_ip = None
	try:
		config["target.ip"] = gethostbyname(section_name)
	except:
		pass
	
	def set_method(method):
		if config["method"] != None and config["method"] != method:
			other_method = config["method"]
			raise Error(f"{section_name} in {filename} has options for multiple methods ({other_method}, {method})")
		
		config["method"] = method
	
	for (attr_name, attr_value) in cfg.items(section_name):
		def attr_host_to_ip():
			try:
				return gethostbyname(attr_value)
				
			except Exception as e:
				raise Error(f"{section_name} {attr_name} option in {filename} cannot be resolved: " + str(e))
		
		def attr_port_number():
			try:
				port = int(attr_value)
				
				if port < 0 or port > 65535:
					raise ValueError(f"port number {port} is out of range")
				
				return port
				
			except ValueError:
				raise Error(f"{section_name} {attr_name} option in {filename} has invalid port number")
		
		if attr_name == "wol.mac":
			set_method("wol")
			
			mac = powerwake.addressutils.normalise_mac(attr_value)
			if mac == None:
				raise Error(f"{section_name} wol.mac option in {filename} has invalid format")
			
			config["wol.mac"] = mac
			
		elif attr_name == "wol.host":
			set_method("wol")
			config["wol.ip"] = attr_host_to_ip()
			
		elif attr_name == "wol.port":
			set_method("wol")
			config["wol.port"] = attr_port_number()
			
		elif attr_name == "ipmi.host":
			set_method("ipmi")
			config["ipmi.host"] = attr_value
			
		elif attr_name == "ipmi.port":
			set_method("ipmi")
			config["ipmi.port"] = attr_port_number()
			
		elif attr_name == "ipmi.username":
			set_method("ipmi")
			config["ipmi.username"] = attr_value
			
		elif attr_name == "ipmi.password":
			set_method("ipmi")
			config["ipmi.password"] = attr_value
			
		else:
			print(f"Ignoring unknown {section_name} option {attr_name} in {filename}", file=sys.stderr)
	
	if config["method"] == "wol":
		if not "wol.mac" in config:
			raise Error(f"{section_name} wol.mac option is not set in {filename}")
	
	elif config["method"] == "ipmi":
		if not "ipmi.host" in config:
			raise Error(f"{section_name} ipmi.host option is not set in {filename}")
	
	if config["method"] != None:
		return config
	else:
		return None

def target_config_from_file(target, filename, gethostbyname = socket.gethostbyname):
	cfg = configparser.ConfigParser()
	cfg.read(filename)
	
	config = None
	
	for section_name in cfg.sections():
		if section_name == target:
			config = target_config_from_hosts_section(filename, gethostbyname, cfg, section_name)
			
		else:
			try:
				section_config = target_config_from_hosts_section(filename, gethostbyname, cfg, section_name)
				
			except Error as e:
				print(str(e), file=sys.stderr)
	
	return config
