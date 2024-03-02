import unittest

from powernap.ActionManager import ActionManager

class TestActionManager(ActionManager):
	__test__ = False

	def __init__(self, actions):
		self.log = []
		super().__init__(actions, "/nonexistant")
	
	def issue_warning(self, action_name, time_remain_secs):
		self.log.append(f"issue_warning({action_name}, {time_remain_secs})")
	
	def rescind_warning(self, action_name):
		self.log.append(f"rescind_warning({action_name})")
	
	def exec_action(self, action_name, param):
		self.log.append(f"exec_action({action_name}, {param})")

class TestPowerNapActionManager(unittest.TestCase):
	def runTest(self):
		am = TestActionManager([
			{ "name": "powersave", "after": 30 },
			{ "name": "poweroff", "after": 600, "warn": 30 },
		])
		
		# 10 minutes pass with the system never going idle.
		am.update(True, 0)
		am.update(True, 600)
		
		self.assertEqual(am.log, [])
		am.log.clear()
		
		# But then it goes idle for 29 seconds.
		am.update(False, 629)
		
		self.assertEqual(am.log, [])
		am.log.clear()
		
		# Saved at the last second before initiating powersave!
		am.update(True, 630)
		
		# This time we let it get to powersave.
		
		am.update(False, 659)
		
		self.assertEqual(am.log, [])
		am.log.clear()
		
		am.update(False, 660)
		
		self.assertEqual(am.log, [
			"exec_action(powersave, true)",
		])
		am.log.clear()
		
		# Hang around idle for a while...
		
		am.update(False, 661)
		am.update(False, 662)
		am.update(False, 663)
		am.update(False, 700)
		am.update(False, 800)
		
		self.assertEqual(am.log, [])
		am.log.clear()
		
		# Someone nudges the mouse, the powersave action should be cancelled.
		
		am.update(True, 900)
		
		self.assertEqual(am.log, [
			"exec_action(powersave, false)",
		])
		am.log.clear()
		
		# This time we leave it longer, first powersave kicks in and
		# then a warning of impending shutdown goes out...
		
		am.update(False, 960)
		
		self.assertEqual(am.log, [
			"exec_action(powersave, true)",
		])
		am.log.clear()
		
		am.update(False, 1472)
		
		self.assertEqual(am.log, [
			"issue_warning(poweroff, 28)",
		])
		am.log.clear()
		
		am.update(False, 1499)
		
		self.assertEqual(am.log, [])
		am.log.clear()
		
		# Caught at the last second, shutdown averted!
		
		am.update(True, 1500)
		
		self.assertEqual(am.log, [
			"exec_action(powersave, false)",
			"rescind_warning(poweroff)",
		])
		am.log.clear()
		
		# This time the system is left alone indefinitely and goes all the way down.
		
		am.update(False, 1600)
		
		self.assertEqual(am.log, [
			"exec_action(powersave, true)",
		])
		am.log.clear()
		
		am.update(False, 2069)
		
		self.assertEqual(am.log, [])
		am.log.clear()
		
		am.update(False, 2070)
		
		self.assertEqual(am.log, [
			"issue_warning(poweroff, 30)",
		])
		am.log.clear()
		
		am.update(False, 2071)
		
		self.assertEqual(am.log, [])
		am.log.clear()
		
		am.update(False, 2099)
		
		self.assertEqual(am.log, [])
		am.log.clear()
		
		am.update(False, 2100)
		
		self.assertEqual(am.log, [
			"exec_action(poweroff, true)",
		])
		am.log.clear()

if __name__ == '__main__':
	unittest.main()
