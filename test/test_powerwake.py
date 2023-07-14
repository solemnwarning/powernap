import tempfile
import unittest

from powerwake import powerwake

class TestPowerWakeDefaultConfig(unittest.TestCase):
	def runTest(self):
		config = tempfile.NamedTemporaryFile()
		config.file.write(b"")
		
		pw = powerwake.PowerWake(config.name)
		
		self.assertEqual(pw.DEBUG, False)
		self.assertEqual(pw.LOG, "")
		self.assertEqual(pw.MONITORS, [])

class TestPowerWakeEnableDebug(unittest.TestCase):
	def runTest(self):
		config = tempfile.NamedTemporaryFile()
		config.file.write(
			b"[powerwake]\n" +
			b"debug = yes\n")
		config.file.flush()
		
		pw = powerwake.PowerWake(config.name)
		
		self.assertEqual(pw.DEBUG, True)
		self.assertEqual(pw.LOG, "")
		self.assertEqual(pw.MONITORS, [])

class TestPowerWakeLogfile(unittest.TestCase):
	def runTest(self):
		config = tempfile.NamedTemporaryFile()
		config.file.write(
			b"[powerwake]\n" +
			b"log = /var/log/powerwaked.log\n")
		config.file.flush()
		
		pw = powerwake.PowerWake(config.name)
		
		self.assertEqual(pw.DEBUG, False)
		self.assertEqual(pw.LOG, "/var/log/powerwaked.log")
		self.assertEqual(pw.MONITORS, [])

class TestPowerWakeMonitorHostsInConfig(unittest.TestCase):
	def runTest(self):
		config = tempfile.NamedTemporaryFile()
		config.file.write(
			b"[ARPMonitor]\n" +
			b"192.168.0.2 = AAbbCCDDEEFF\n" +
			b"192.168.0.3 = 01:23:45:67:89:0A\n")
		config.file.flush()
		
		pw = powerwake.PowerWake(config.name)
		
		self.assertEqual(pw.MONITORS, [
			{
				"monitor": "ARPMonitor",
				"cache": {
					"192.168.0.2": "aabbccddeeff",
					"192.168.0.3": "01234567890a",
				},
			} ])

class TestPowerWakeMonitorHostsInFile(unittest.TestCase):
	def runTest(self):
		cache = tempfile.NamedTemporaryFile()
		cache.file.write(
			b"12:34:56:78:90:ab 192.168.0.1\n" +
			b"AA:BB:CC:DD:EE:FF 192.168.0.2\n")
		cache.file.flush()
		
		config = tempfile.NamedTemporaryFile()
		config.file.write(
			b"[ARPMonitor]\n" +
			b"file = " + bytes(cache.name, "ascii") + b"\n")
		config.file.flush()
		
		pw = powerwake.PowerWake(config.name)
		
		self.assertEqual(pw.MONITORS, [
			{
				"monitor": "ARPMonitor",
				"cache": {
					"192.168.0.1": "1234567890ab",
					"192.168.0.2": "aabbccddeeff",
				},
			} ])

class TestPowerWakeUnknownSection(unittest.TestCase):
	def runTest(self):
		config = tempfile.NamedTemporaryFile()
		config.file.write(
			b"[powerwake2]\n")
		config.file.flush()
		
		with self.assertRaisesRegex(Exception, "Unexpected \\[powerwake2\\] section in ") as e:
			pw = powerwake.PowerWake(config.name)

class TestPowerWakeUnknownValue(unittest.TestCase):
	def runTest(self):
		config = tempfile.NamedTemporaryFile()
		config.file.write(
			b"[powerwake]\n" +
			b"foo = bar\n")
		config.file.flush()
		
		with self.assertRaisesRegex(Exception, "Unexpected value 'foo' in \\[powerwake\\] section in ") as e:
			pw = powerwake.PowerWake(config.name)

class TestPowerWakeInvalidIP(unittest.TestCase):
	def runTest(self):
		config = tempfile.NamedTemporaryFile()
		config.file.write(
			b"[ARPMonitor]\n" +
			b"192.168.0. = aa:bb:cc:dd:ee:ff\n")
		config.file.flush()
		
		with self.assertRaisesRegex(Exception, "Unexpected value '192.168.0.' in \\[ARPMonitor\\] section \\(expected 'file' or an IP address\\) in ") as e:
			pw = powerwake.PowerWake(config.name)

class TestPowerWakeInvalidMAC(unittest.TestCase):
	def runTest(self):
		config = tempfile.NamedTemporaryFile()
		config.file.write(
			b"[ARPMonitor]\n" +
			b"192.168.0.1 = aa:bb:cc:dd:e:ff\n")
		config.file.flush()
		
		with self.assertRaisesRegex(Exception, "Unexpected value 'aa:bb:cc:dd:e:ff' in \\[ARPMonitor\\] section \\(expected a MAC address\\) in ") as e:
			pw = powerwake.PowerWake(config.name)

if __name__ == '__main__':
	unittest.main()
