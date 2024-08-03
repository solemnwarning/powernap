import unittest

import powerwake.addressutils

class TestPowerWakeNormaliseMAC(unittest.TestCase):
	def runTest(self):
		# Hex string
		self.assertEqual(powerwake.addressutils.normalise_mac("0123456789AB"),  "0123456789ab")
		self.assertEqual(powerwake.addressutils.normalise_mac("0123456789ab"),  "0123456789ab")
		self.assertEqual(powerwake.addressutils.normalise_mac("0123456789A"),    None)
		self.assertEqual(powerwake.addressutils.normalise_mac("0123456789ABC"),  None)
		self.assertEqual(powerwake.addressutils.normalise_mac("XXXXXXXXXXXX"),   None)
		self.assertEqual(powerwake.addressutils.normalise_mac(""),               None)
		
		# Colon seperated bytes
		self.assertEqual(powerwake.addressutils.normalise_mac("01:23:45:67:89:AB"),    "0123456789ab")
		self.assertEqual(powerwake.addressutils.normalise_mac("1:23:45:6:89:AB"),      "0123450689ab")
		self.assertEqual(powerwake.addressutils.normalise_mac("01:23:45:67:89:"),       None)
		self.assertEqual(powerwake.addressutils.normalise_mac("01:23:45:67:89"),        None)
		self.assertEqual(powerwake.addressutils.normalise_mac("01:23:45:67:89:ABC"),    None)
		self.assertEqual(powerwake.addressutils.normalise_mac("01:23:45:67:89:AB:CD"),  None)
		
		# Dot seperated bytes
		self.assertEqual(powerwake.addressutils.normalise_mac("01.23.45.67.89.AB"),    "0123456789ab")
		self.assertEqual(powerwake.addressutils.normalise_mac("1.23.45.6.89.AB"),      "0123450689ab")
		self.assertEqual(powerwake.addressutils.normalise_mac("01.23..67.89.AB"),       None)
		self.assertEqual(powerwake.addressutils.normalise_mac("01.23.45.67.89"),        None)
		self.assertEqual(powerwake.addressutils.normalise_mac("01.23.45.67.89.ABC"),    None)
		self.assertEqual(powerwake.addressutils.normalise_mac("01.23.45.67.89.AB.CD"),  None)
		
		# Dash seperated bytes
		self.assertEqual(powerwake.addressutils.normalise_mac("01-23-45-67-89-AB"),    "0123456789ab")
		self.assertEqual(powerwake.addressutils.normalise_mac("1-23-45-6-89-AB"),      "0123450689ab")
		self.assertEqual(powerwake.addressutils.normalise_mac("01-23-45--89-AB"),       None)
		self.assertEqual(powerwake.addressutils.normalise_mac("01-23-45-67-89"),        None)
		self.assertEqual(powerwake.addressutils.normalise_mac("01-23-45-67-89-ABC"),    None)
		self.assertEqual(powerwake.addressutils.normalise_mac("01-23-45-67-89-AB-CD"),  None)
		
		# Mixing address formats isn't permitted
		self.assertEqual(powerwake.addressutils.normalise_mac("01-23:45.67-89-AB"), None)
