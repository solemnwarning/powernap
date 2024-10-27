import re
import tempfile
import unittest

import powerwake.targetconfig

def mock_gethostbyname(name):
	if re.fullmatch(r'\d+\.\d+\.\d+\.\d+', name):
		# Looks like an IP address
		return name
	
	elif name == "host1.example.com":
		return "1.2.3.4"
	
	elif name == "host2.example.com":
		return "5.6.7.8"
	
	else:
		raise Exception(f"Host not known: {name}")

MOCK_ETHERS_FILE = (
	b"# host1.example.com / 1.2.3.4\n" +
	b"1:23:45:67:89:AB  1.2.3.4\n" +
	b"\n" +
	b"# host2.example.com / 5.6.7.8\n" +
	b"AB:CD:EF:1:23:45  host2.example.com\n" +
	b"\n" +
	b"# host3.example.com / NO IP\n" +
	b"AA:BB:CC:DD:EE:FF  host3.example.com\n"
)

class TestPowerWakeParseRFC1464(unittest.TestCase):
	def runTest(self):
		# Basic name=value pair
		
		name, value = powerwake.targetconfig.parse_rfc1464_attribute("hellish=advice")
		
		self.assertEqual(name,  "hellish")
		self.assertEqual(value, "advice")
		
		# Special characters in the value should be treated as plain text and no special
		# processing or decoding applied.
		
		name, value = powerwake.targetconfig.parse_rfc1464_attribute("bag=want=crush")
		
		self.assertEqual(name,  "bag")
		self.assertEqual(value, "want=crush")
		
		name, value = powerwake.targetconfig.parse_rfc1464_attribute("distribution=``ossif`i`=ed")
		
		self.assertEqual(name,  "distribution")
		self.assertEqual(value, "``ossif`i`=ed")
		
		# Un-escaped leading and trailing whitespace in the attribute name should be
		# discarded, any leading/trailing whitespace in the value should be preserved.
		
		name, value = powerwake.targetconfig.parse_rfc1464_attribute(" im partial = repeat ")
		
		self.assertEqual(name,  "im partial")
		self.assertEqual(value, " repeat ")
		
		# Escaped characters in the attribute name should be decoded.
		
		name, value = powerwake.targetconfig.parse_rfc1464_attribute("wise`=books=unequaled")
		
		self.assertEqual(name,  "wise=books")
		self.assertEqual(value, "unequaled")
		
		name, value = powerwake.targetconfig.parse_rfc1464_attribute("r``est=nappy")
		
		self.assertEqual(name,  "r`est")
		self.assertEqual(value, "nappy")
		
		# Escaped leading and trailing whitespace in the attribute name should be
		# preserved and decoded.
		
		name, value = powerwake.targetconfig.parse_rfc1464_attribute(" ` business` ` =fly")
		
		self.assertEqual(name,  " business  ")
		self.assertEqual(value, "fly")

class TestPowerWakeTargetDefaultMethodInDNS(unittest.TestCase):
	def runTest(self):
		config = powerwake.targetconfig.parse_dns_result("crayon.example.com", "192.168.0.1", {
			"powerwake.wol.mac": "ab:cd:ef:01:23:45",
		})
		
		self.assertEqual(config, {
			"target": "crayon.example.com",
			"target.ip": "192.168.0.1",
			"method": "wol",
			"wol.mac": "abcdef012345",
			"wait": False
		})

class TestPowerWakeTargetNoIPInDNS(unittest.TestCase):
	def runTest(self):
		config = powerwake.targetconfig.parse_dns_result("place.example.com", None, {
			"powerwake.wol.mac": "ab:cd:ef:01:23:45",
		})
		
		self.assertEqual(config, {
			"target": "place.example.com",
			"method": "wol",
			"wol.mac": "abcdef012345",
			"wait": False
		})

class TestPowerWakeTargetCustomWOLHostInDNS(unittest.TestCase):
	def runTest(self):
		config = powerwake.targetconfig.parse_dns_result("awesome.example.com", "192.168.0.1", {
			"powerwake.method": "wol",
			"powerwake.wol.mac": "ab:cd:ef:01:23:45",
			"powerwake.wol.host": "localhost",
			"powerwake.wol.port": "1234",
		})
		
		self.assertEqual(config, {
			"target": "awesome.example.com",
			"target.ip": "192.168.0.1",
			"method": "wol",
			"wol.mac": "abcdef012345",
			"wol.ip": "127.0.0.1",
			"wol.port": 1234,
			"wait": False,
		})

class TestPowerWakeTargetBadWOLHostInDNS(unittest.TestCase):
	def runTest(self):
		with self.assertRaisesRegex(powerwake.targetconfig.Error, r"powerwake\.wol\.host attribute cannot be resolved") as e:
			powerwake.targetconfig.parse_dns_result("sedate.example.com", "192.168.0.1", {
				"powerwake.method": "wol",
				"powerwake.wol.mac": "ab:cd:ef:01:23:45",
				"powerwake.wol.host": "nosuchhost.example.com",
				"powerwake.wol.port": "1234",
			})

class TestPowerWakeTargetBadWOLPortInDNS(unittest.TestCase):
	def runTest(self):
		with self.assertRaises(powerwake.targetconfig.Error) as cm:
			powerwake.targetconfig.parse_dns_result("sedate.example.com", "192.168.0.1", {
				"powerwake.method": "wol",
				"powerwake.wol.mac": "ab:cd:ef:01:23:45",
				"powerwake.wol.host": "localhost",
				"powerwake.wol.port": "potato",
			})
		
		self.assertEqual(str(cm.exception), "sedate.example.com powerwake.wol.port attribute has invalid port number")

class TestPowerWakeTargetMacNoSeperator(unittest.TestCase):
	def runTest(self):
		config = powerwake.targetconfig.parse_dns_result("icicle.example.com", None, {
			"powerwake.wol.mac": "abcdef012345",
		})
		
		self.assertEqual(config, {
			"target": "icicle.example.com",
			"method": "wol",
			"wol.mac": "abcdef012345",
			"wait": False
		})

class TestPowerWakeTargetDashSeperator(unittest.TestCase):
	def runTest(self):
		config = powerwake.targetconfig.parse_dns_result("slave.example.com", None, {
			"powerwake.wol.mac": "ab-cd-ef-1-23-45",
		})
		
		self.assertEqual(config, {
			"target": "slave.example.com",
			"method": "wol",
			"wol.mac": "abcdef012345",
			"wait": False
		})

class TestPowerWakeTargetIPMIPartialConfigInDNS(unittest.TestCase):
	def runTest(self):
		config = powerwake.targetconfig.parse_dns_result("chivalrous.example.com", None, {
			"powerwake.ipmi.host": "ipmi.chivalrous.example.com",
		})
		
		self.assertEqual(config, {
			"target": "chivalrous.example.com",
			"method": "ipmi",
			"ipmi.host": "ipmi.chivalrous.example.com",
			"wait": False,
		})

class TestPowerWakeTargetIPMIFullConfigInDNS(unittest.TestCase):
	def runTest(self):
		config = powerwake.targetconfig.parse_dns_result("sticks.example.com", "99.99.99.99", {
			"powerwake.ipmi.host": "ipmi.sticks.example.com",
			"powerwake.ipmi.port": "999",
			"powerwake.ipmi.username": "bob",
			"powerwake.ipmi.password": "hunter2",
		})
		
		self.assertEqual(config, {
			"target": "sticks.example.com",
			"target.ip": "99.99.99.99",
			"method": "ipmi",
			"ipmi.host": "ipmi.sticks.example.com",
			"ipmi.port": 999,
			"ipmi.username": "bob",
			"ipmi.password": "hunter2",
			"wait": False,
		})

class TestPowerWakeTargetIPMIEmptyPortInDNS(unittest.TestCase):
	def runTest(self):
		with self.assertRaises(powerwake.targetconfig.Error) as cm:
			powerwake.targetconfig.parse_dns_result("rate.example.com", "99.99.99.99", {
				"powerwake.ipmi.host": "ipmi.rate.example.com",
				"powerwake.ipmi.port": "",
			})
		
		self.assertEqual(str(cm.exception), "rate.example.com powerwake.ipmi.port attribute has invalid port number")

class TestPowerWakeTargetIPMIHighPortInDNS(unittest.TestCase):
	def runTest(self):
		with self.assertRaises(powerwake.targetconfig.Error) as cm:
			powerwake.targetconfig.parse_dns_result("periodic.example.com", "99.99.99.99", {
				"powerwake.ipmi.host": "ipmi.periodic.example.com",
				"powerwake.ipmi.port": "99999",
			})
		
		self.assertEqual(str(cm.exception), "periodic.example.com powerwake.ipmi.port attribute has invalid port number")

class TestPowerWakeTargetIPMIAndWOL(unittest.TestCase):
	def runTest(self):
		with self.assertRaises(powerwake.targetconfig.Error) as cm:
			powerwake.targetconfig.parse_dns_result("selection.example.com", "99.99.99.99", {
				"powerwake.wol.mac": "ab:cd:ef:01:23:45",
				"powerwake.ipmi.host": "ipmi.selection.example.com",
			})
		
		self.assertEqual(str(cm.exception), "selection.example.com has attributes for multiple methods (wol, ipmi)")

class TestPowerWakeTargetExtraFieldsInDNS(unittest.TestCase):
	def runTest(self):
		config = powerwake.targetconfig.parse_dns_result("unequaled.example.com", None, {
			"powerwake.wol.mac": "ab:cd:ef:01:23:45",
			"hello": "world",
		})
		
		self.assertEqual(config, {
			"target": "unequaled.example.com",
			"method": "wol",
			"wol.mac": "abcdef012345",
			"wait": False
		})

class TestPowerWakeTargetNoPowerwakeFields(unittest.TestCase):
	def runTest(self):
		config = powerwake.targetconfig.parse_dns_result("dark.example.com", None, {
			"hello": "world",
		})
		
		self.assertEqual(config, None)

class TestPowerWakeEthersIPMatchedByIP(unittest.TestCase):
	def runTest(self):
		ethers = tempfile.NamedTemporaryFile()
		ethers.file.write(MOCK_ETHERS_FILE)
		ethers.file.flush()
		
		config = powerwake.targetconfig.target_config_from_ethers("1.2.3.4", ethers.name, mock_gethostbyname)
		
		self.assertEqual(config, {
			"target": "1.2.3.4",
			"target.ip": "1.2.3.4",
			"method": "wol",
			"wol.mac": "0123456789ab",
			"wait": False
		})

class TestPowerWakeEthersIPMatchedByName(unittest.TestCase):
	def runTest(self):
		ethers = tempfile.NamedTemporaryFile()
		ethers.file.write(MOCK_ETHERS_FILE)
		ethers.file.flush()
		
		config = powerwake.targetconfig.target_config_from_ethers("host1.example.com", ethers.name, mock_gethostbyname)
		
		self.assertEqual(config, {
			"target": "host1.example.com",
			"target.ip": "1.2.3.4",
			"method": "wol",
			"wol.mac": "0123456789ab",
			"wait": False
		})

class TestPowerWakeEthersIPMatchedByMAC(unittest.TestCase):
	def runTest(self):
		ethers = tempfile.NamedTemporaryFile()
		ethers.file.write(MOCK_ETHERS_FILE)
		ethers.file.flush()
		
		config = powerwake.targetconfig.target_config_from_ethers("01-23-45-67-89-AB", ethers.name, mock_gethostbyname)
		
		self.assertEqual(config, {
			"target": "01-23-45-67-89-AB",
			"target.ip": "1.2.3.4",
			"method": "wol",
			"wol.mac": "0123456789ab",
			"wait": False
		})

class TestPowerWakeEthersNameMatchedByIP(unittest.TestCase):
	def runTest(self):
		ethers = tempfile.NamedTemporaryFile()
		ethers.file.write(MOCK_ETHERS_FILE)
		ethers.file.flush()
		
		config = powerwake.targetconfig.target_config_from_ethers("5.6.7.8", ethers.name, mock_gethostbyname)
		
		self.assertEqual(config, {
			"target": "5.6.7.8",
			"target.ip": "5.6.7.8",
			"method": "wol",
			"wol.mac": "abcdef012345",
			"wait": False
		})

class TestPowerWakeEthersNameMatchedByName(unittest.TestCase):
	def runTest(self):
		ethers = tempfile.NamedTemporaryFile()
		ethers.file.write(MOCK_ETHERS_FILE)
		ethers.file.flush()
		
		config = powerwake.targetconfig.target_config_from_ethers("host2.example.com", ethers.name, mock_gethostbyname)
		
		self.assertEqual(config, {
			"target": "host2.example.com",
			"target.ip": "5.6.7.8",
			"method": "wol",
			"wol.mac": "abcdef012345",
			"wait": False
		})

class TestPowerWakeEthersNameMatchedByMAC(unittest.TestCase):
	def runTest(self):
		ethers = tempfile.NamedTemporaryFile()
		ethers.file.write(MOCK_ETHERS_FILE)
		ethers.file.flush()
		
		config = powerwake.targetconfig.target_config_from_ethers("AB:CD:EF:01:23:45", ethers.name, mock_gethostbyname)
		
		self.assertEqual(config, {
			"target": "AB:CD:EF:01:23:45",
			"target.ip": "5.6.7.8",
			"method": "wol",
			"wol.mac": "abcdef012345",
			"wait": False
		})

class TestPowerWakeEthersNameWithoutIPMatchedByName(unittest.TestCase):
	def runTest(self):
		ethers = tempfile.NamedTemporaryFile()
		ethers.file.write(MOCK_ETHERS_FILE)
		ethers.file.flush()
		
		config = powerwake.targetconfig.target_config_from_ethers("host3.example.com", ethers.name, mock_gethostbyname)
		
		self.assertEqual(config, {
			"target": "host3.example.com",
			"method": "wol",
			"wol.mac": "aabbccddeeff",
			"wait": False
		})

class TestPowerWakeEthersNameWithoutIPMatchedByMAC(unittest.TestCase):
	def runTest(self):
		ethers = tempfile.NamedTemporaryFile()
		ethers.file.write(MOCK_ETHERS_FILE)
		ethers.file.flush()
		
		config = powerwake.targetconfig.target_config_from_ethers("aabbccddeeff", ethers.name, mock_gethostbyname)
		
		self.assertEqual(config, {
			"target": "aabbccddeeff",
			"method": "wol",
			"wol.mac": "aabbccddeeff",
			"wait": False
		})

class TestPowerWakeEthersNoMatchByIP(unittest.TestCase):
	def runTest(self):
		ethers = tempfile.NamedTemporaryFile()
		ethers.file.write(MOCK_ETHERS_FILE)
		ethers.file.flush()
		
		config = powerwake.targetconfig.target_config_from_ethers("8.8.8.8", ethers.name, mock_gethostbyname)
		
		self.assertEqual(config, None)

class TestPowerWakeEthersNoMatchByIP(unittest.TestCase):
	def runTest(self):
		ethers = tempfile.NamedTemporaryFile()
		ethers.file.write(MOCK_ETHERS_FILE)
		ethers.file.flush()
		
		config = powerwake.targetconfig.target_config_from_ethers("8.8.8.8", ethers.name, mock_gethostbyname)
		
		self.assertEqual(config, None)

class TestPowerWakeEthersNoMatchByName(unittest.TestCase):
	def runTest(self):
		ethers = tempfile.NamedTemporaryFile()
		ethers.file.write(MOCK_ETHERS_FILE)
		ethers.file.flush()
		
		config = powerwake.targetconfig.target_config_from_ethers("hostX.example.com", ethers.name, mock_gethostbyname)
		
		self.assertEqual(config, None)

class TestPowerWakeHostsFileMatch(unittest.TestCase):
	def runTest(self):
		HOSTS_CONTENT = (
			b"[host1.example.com]\n" +
			b"wol.mac = AA:BB:CC:DD:EE:FF\n" +
			b"wol.port = 999\n"
		)
		
		hosts = tempfile.NamedTemporaryFile()
		hosts.file.write(HOSTS_CONTENT)
		hosts.file.flush()
		
		config = powerwake.targetconfig.target_config_from_file("host1.example.com", hosts.name, mock_gethostbyname)
		
		self.assertEqual(config, {
			"target": "host1.example.com",
			"target.ip": "1.2.3.4", # From "DNS"
			"method": "wol",
			"wol.mac": "aabbccddeeff",
			"wol.port": 999,
			"wait": False
		})

class TestPowerWakeHostsFileMatchNoIP(unittest.TestCase):
	def runTest(self):
		HOSTS_CONTENT = (
			b"[hostX.example.com]\n" +
			b"wol.mac = AA:BB:CC:DD:EE:FF\n"
		)
		
		hosts = tempfile.NamedTemporaryFile()
		hosts.file.write(HOSTS_CONTENT)
		hosts.file.flush()
		
		config = powerwake.targetconfig.target_config_from_file("hostX.example.com", hosts.name, mock_gethostbyname)
		
		self.assertEqual(config, {
			"target": "hostX.example.com",
			"method": "wol",
			"wol.mac": "aabbccddeeff",
			"wait": False
		})

class TestPowerWakeHostsFileNoMatch(unittest.TestCase):
	def runTest(self):
		HOSTS_CONTENT = (
			b"[host1.example.com]\n" +
			b"wol.mac = AA:BB:CC:DD:EE:FF\n"
		)
		
		hosts = tempfile.NamedTemporaryFile()
		hosts.file.write(HOSTS_CONTENT)
		hosts.file.flush()
		
		config = powerwake.targetconfig.target_config_from_file("host2.example.com", hosts.name, mock_gethostbyname)
		
		self.assertEqual(config, None)

class TestPowerWakeHostsFileBadPort(unittest.TestCase):
	def runTest(self):
		HOSTS_CONTENT = (
			b"[host1.example.com]\n" +
			b"wol.mac = AA:BB:CC:DD:EE:FF\n" +
			b"wol.port = 99999\n"
		)
		
		hosts = tempfile.NamedTemporaryFile()
		hosts.file.write(HOSTS_CONTENT)
		hosts.file.flush()
		
		with self.assertRaises(powerwake.targetconfig.Error) as cm:
			powerwake.targetconfig.target_config_from_file("host1.example.com", hosts.name, mock_gethostbyname)
		
		self.assertEqual(str(cm.exception), f"host1.example.com wol.port option in {hosts.name} has invalid port number")

class TestPowerWakeHostsFileBadPortInOtherSection(unittest.TestCase):
	def runTest(self):
		HOSTS_CONTENT = (
			b"[host1.example.com]\n" +
			b"wol.mac = AA:BB:CC:DD:EE:FF\n" +
			b"[host2.example.com]\n" +
			b"wol.mac = 00:11:22:33:44:55\n" +
			b"wol.port = 99999\n"
		)
		
		hosts = tempfile.NamedTemporaryFile()
		hosts.file.write(HOSTS_CONTENT)
		hosts.file.flush()
		
		config = powerwake.targetconfig.target_config_from_file("host1.example.com", hosts.name, mock_gethostbyname)
		
		self.assertEqual(config, {
			"target": "host1.example.com",
			"target.ip": "1.2.3.4", # From "DNS"
			"method": "wol",
			"wol.mac": "aabbccddeeff",
			"wait": False
		})

class TestPowerWakeHostsFileIPMIFull(unittest.TestCase):
	def runTest(self):
		HOSTS_CONTENT = (
			b"[host1.example.com]\n" +
			b"ipmi.host = ipmi.host1.example.com\n" +
			b"ipmi.port = 999\n" +
			b"ipmi.username = OPERATOR\n" +
			b"ipmi.password = password123\n"
		)
		
		hosts = tempfile.NamedTemporaryFile()
		hosts.file.write(HOSTS_CONTENT)
		hosts.file.flush()
		
		config = powerwake.targetconfig.target_config_from_file("host1.example.com", hosts.name, mock_gethostbyname)
		
		self.assertEqual(config, {
			"target": "host1.example.com",
			"target.ip": "1.2.3.4",
			"method": "ipmi",
			"ipmi.host": "ipmi.host1.example.com",
			"ipmi.port": 999,
			"ipmi.username": "OPERATOR",
			"ipmi.password": "password123",
			"wait": False,
		})

class TestPowerWakeHostsFileIPMIPartial(unittest.TestCase):
	def runTest(self):
		HOSTS_CONTENT = (
			b"[host1.example.com]\n" +
			b"ipmi.host = ipmi.host1.example.com\n" +
			b"ipmi.username = OPERATOR\n"
		)
		
		hosts = tempfile.NamedTemporaryFile()
		hosts.file.write(HOSTS_CONTENT)
		hosts.file.flush()
		
		config = powerwake.targetconfig.target_config_from_file("host1.example.com", hosts.name, mock_gethostbyname)
		
		self.assertEqual(config, {
			"target": "host1.example.com",
			"target.ip": "1.2.3.4",
			"method": "ipmi",
			"ipmi.host": "ipmi.host1.example.com",
			"ipmi.username": "OPERATOR",
			"wait": False,
		})

class TestPowerWakeHostsFileConflictingMethods(unittest.TestCase):
	def runTest(self):
		HOSTS_CONTENT = (
			b"[host1.example.com]\n" +
			b"wol.mac = AA:BB:CC:DD:EE:FF\n" +
			b"ipmi.host = ipmi.host1.example.com\n"
		)
		
		hosts = tempfile.NamedTemporaryFile()
		hosts.file.write(HOSTS_CONTENT)
		hosts.file.flush()
		
		with self.assertRaises(powerwake.targetconfig.Error) as cm:
			powerwake.targetconfig.target_config_from_file("host1.example.com", hosts.name, mock_gethostbyname)
		
		self.assertEqual(str(cm.exception), f"host1.example.com in {hosts.name} has options for multiple methods (wol, ipmi)")

class TestPowerWakeHostsFileCustomWOLIP(unittest.TestCase):
	def runTest(self):
		HOSTS_CONTENT = (
			b"[host1.example.com]\n" +
			b"wol.mac = AA:BB:CC:DD:EE:FF\n" +
			b"wol.host = host2.example.com\n"
		)
		
		hosts = tempfile.NamedTemporaryFile()
		hosts.file.write(HOSTS_CONTENT)
		hosts.file.flush()
		
		config = powerwake.targetconfig.target_config_from_file("host1.example.com", hosts.name, mock_gethostbyname)
		
		self.assertEqual(config, {
			"target": "host1.example.com",
			"target.ip": "1.2.3.4", # From "DNS"
			"method": "wol",
			"wol.mac": "aabbccddeeff",
			"wol.ip": "5.6.7.8",
			"wait": False
		})

class TestPowerWakeHostsFileBadWOLIP(unittest.TestCase):
	def runTest(self):
		HOSTS_CONTENT = (
			b"[host1.example.com]\n" +
			b"wol.mac = AA:BB:CC:DD:EE:FF\n" +
			b"wol.host = nosuchhost.example.com\n"
		)
		
		hosts = tempfile.NamedTemporaryFile()
		hosts.file.write(HOSTS_CONTENT)
		hosts.file.flush()
		
		with self.assertRaises(powerwake.targetconfig.Error) as cm:
			powerwake.targetconfig.target_config_from_file("host1.example.com", hosts.name, mock_gethostbyname)
		
		self.assertEqual(str(cm.exception), f"host1.example.com wol.host option in {hosts.name} cannot be resolved: Host not known: nosuchhost.example.com")
