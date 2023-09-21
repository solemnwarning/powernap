import re
import tempfile
import unittest

from powernap.ConfigReader import ConfigReader

class TestPowerNapDefaultConfig(unittest.TestCase):
	def runTest(self):
		config = tempfile.NamedTemporaryFile()
		config.file.write(b"")
		config.file.flush()
		
		cr = ConfigReader([ "poweroff", "suspend", "powersave" ])
		c = cr.read_config(config.name)
		
		self.assertEqual(c["actions"],  [])
		self.assertEqual(c["interval"], 1)
		self.assertEqual(c["monitors"], [])

class TestPowerNapSpecifyActions(unittest.TestCase):
	def runTest(self):
		config = tempfile.NamedTemporaryFile()
		config.file.write(
			b"action powersave after 30s\n" +
			b"action poweroff after 5m warn 1m30s\n")
		config.file.flush()
		
		cr = ConfigReader([ "poweroff", "suspend", "powersave" ])
		c = cr.read_config(config.name)
		
		self.assertEqual(c["actions"], [
			{ "name": "powersave", "after": 30 },
			{ "name": "poweroff", "after": 300, "warn": 90 } ])

class TestPowerNapSpecifyActionNoTime(unittest.TestCase):
	def runTest(self):
		config = tempfile.NamedTemporaryFile()
		config.file.write(
			b"action powersave\n")
		config.file.flush()
		
		cr = ConfigReader([ "poweroff", "suspend", "powersave" ])
		
		with self.assertRaisesRegex(Exception, f"No after option specified for action powersave at {config.name} line 1") as e:
			cr.read_config(config.name)

class TestPowerNapSpecifyMonitors(unittest.TestCase):
	def runTest(self):
		config = tempfile.NamedTemporaryFile()
		config.file.write(
			b"monitor disk hda\n" +
			b"monitor keyboard\n" +
			b"monitor load 1.5\n" +
			b"monitor powerwake\n" +
			b"monitor powerwake port 1234\n" +
			b"monitor process ^/sbin/init foo\n" +
			b"monitor process-io samba\n" +
			b"monitor tcp port 80\n" +
			b"monitor udp port 53\n" +
			b"monitor wol port 9\n")
		config.file.flush()
		
		cr = ConfigReader([ "poweroff", "suspend", "powersave" ])
		c = cr.read_config(config.name)
		
		self.assertEqual(c["monitors"], [
			{ "type": "disk", "device": "hda" },
			{ "type": "keyboard" },
			{ "type": "load", "threshold": 1.5 },
			{ "type": "powerwake", "port": 57748 },
			{ "type": "powerwake", "port": 1234 },
			{ "type": "process", "regex": re.compile("^/sbin/init foo") },
			{ "type": "process-io", "regex": re.compile("samba") },
			{ "type": "tcp", "port": 80 },
			{ "type": "udp", "port": 53 },
			{ "type": "wol", "port": 9 } ])

class TestPowerNapDiskMonitorNoDevice(unittest.TestCase):
	def runTest(self):
		config = tempfile.NamedTemporaryFile()
		config.file.write(
			b"monitor disk\n")
		config.file.flush()
		
		cr = ConfigReader([ "poweroff", "suspend", "powersave" ])
		
		with self.assertRaisesRegex(Exception, f"Expected device name after 'disk' at {config.name} line 1") as e:
			cr.read_config(config.name)

class TestPowerNapInputMonitorOptions(unittest.TestCase):
	def runTest(self):
		config = tempfile.NamedTemporaryFile()
		config.file.write(
			b"monitor keyboard stuff things\n")
		config.file.flush()
		
		cr = ConfigReader([ "poweroff", "suspend", "powersave" ])
		
		with self.assertRaisesRegex(Exception, f"Unexpected 'stuff things' after 'keyboard' at {config.name} line 1") as e:
			cr.read_config(config.name)

class TestPowerNapPWMonitorNoPortKeyword(unittest.TestCase):
	def runTest(self):
		config = tempfile.NamedTemporaryFile()
		config.file.write(
			b"monitor powerwake 1234\n")
		config.file.flush()
		
		cr = ConfigReader([ "poweroff", "suspend", "powersave" ])
		
		with self.assertRaisesRegex(Exception, f"Expected 'port <port number>' after 'powerwake' at {config.name} line 1") as e:
			cr.read_config(config.name)

class TestPowerNapPWMonitorBadPort(unittest.TestCase):
	def runTest(self):
		config = tempfile.NamedTemporaryFile()
		config.file.write(
			b"monitor powerwake port hello\n")
		config.file.flush()
		
		cr = ConfigReader([ "poweroff", "suspend", "powersave" ])
		
		with self.assertRaisesRegex(Exception, f"Expected 'port <port number>' after 'powerwake' at {config.name} line 1") as e:
			cr.read_config(config.name)

class TestPowerNapPWMonitorOutOfRangePort(unittest.TestCase):
	def runTest(self):
		config = tempfile.NamedTemporaryFile()
		config.file.write(
			b"monitor powerwake port 1000000\n")
		config.file.flush()
		
		cr = ConfigReader([ "poweroff", "suspend", "powersave" ])
		
		with self.assertRaisesRegex(Exception, f"Invalid port number 1000000 at {config.name} line 1") as e:
			cr.read_config(config.name)

class TestPowerNapUsersMonitor(unittest.TestCase):
	def runTest(self):
		config = tempfile.NamedTemporaryFile()
		config.file.write(
			b"monitor users")
		config.file.flush()
		
		cr = ConfigReader([ "poweroff", "suspend", "powersave" ])
		c = cr.read_config(config.name)
		
		self.assertEqual(c["monitors"], [
			{ "type": "users", "max_idle_secs": None } ])

class TestPowerNapUsersMonitorMaxIdle(unittest.TestCase):
	def runTest(self):
		config = tempfile.NamedTemporaryFile()
		config.file.write(
			b"monitor users max-idle 30m")
		config.file.flush()
		
		cr = ConfigReader([ "poweroff", "suspend", "powersave" ])
		c = cr.read_config(config.name)
		
		self.assertEqual(c["monitors"], [
			{ "type": "users", "max_idle_secs": 1800 } ])

class TestPowerNapUsersMonitorMaxIdleNoDuration(unittest.TestCase):
	def runTest(self):
		config = tempfile.NamedTemporaryFile()
		config.file.write(
			b"monitor users max-idle")
		config.file.flush()
		
		cr = ConfigReader([ "poweroff", "suspend", "powersave" ])
		
		with self.assertRaisesRegex(Exception, f"Expected a time duration \\(e.g. 1m\\) after 'max-idle' at {config.name} line 1") as e:
			cr.read_config(config.name)

class TestPowerNapUsersMonitorMaxIdleTwice(unittest.TestCase):
	def runTest(self):
		config = tempfile.NamedTemporaryFile()
		config.file.write(
			b"monitor users max-idle 1m max-idle 30m")
		config.file.flush()
		
		cr = ConfigReader([ "poweroff", "suspend", "powersave" ])
		
		with self.assertRaisesRegex(Exception, f"Unexpected 'max-idle 30m' after '1m' at {config.name} line 1") as e:
			cr.read_config(config.name)

if __name__ == '__main__':
	unittest.main()
