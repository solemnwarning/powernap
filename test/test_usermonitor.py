import unittest

#import logging
#logging.basicConfig(level=logging.DEBUG)

from powernap.monitors.LoggedInUsersMonitor import LoggedInUsersMonitor

class TestLoggedInUsersMonitorNoUsers(unittest.TestCase):
	def runTest(self):
		monitor = LoggedInUsersMonitor(None)
		
		w_output = ""
		
		self.assertEqual(monitor._check_w_output(w_output), False)

class TestLoggedInUsersMonitorConsoleUser(unittest.TestCase):
	def runTest(self):
		monitor = LoggedInUsersMonitor(None)
		
		w_output = "root     tty1     -                 2days -bash"
		
		self.assertEqual(monitor._check_w_output(w_output), True)

class TestLoggedInUsersMonitorShortIdleConsoleUser(unittest.TestCase):
	def runTest(self):
		monitor = LoggedInUsersMonitor(259200) # 3 days
		
		w_output = "root     tty1     -                 2days -bash"
		
		self.assertEqual(monitor._check_w_output(w_output), True)

class TestLoggedInUsersMonitorLongIdleConsoleUser(unittest.TestCase):
	def runTest(self):
		monitor = LoggedInUsersMonitor(86400) # 1 day
		
		w_output = "root     tty1     -                 2days -bash"
		
		self.assertEqual(monitor._check_w_output(w_output), False)

class TestLoggedInUsersMonitorX11User(unittest.TestCase):
	def runTest(self):
		monitor = LoggedInUsersMonitor(None)
		
		w_output = "solemnwa console  :0                8days -:0"
		
		self.assertEqual(monitor._check_w_output(w_output), True)

class TestLoggedInUsersMonitorRemoteUsers(unittest.TestCase):
	def runTest(self):
		monitor = LoggedInUsersMonitor(None)
		
		w_output = '''
solemnwa pts/2    172.24.128.21    44:29  screen -dUx i
solemnwa pts/1    :pts/2:S.0       44:29  irssi
solemnwa pts/3    172.24.128.21    18:49m screen -dUx r
solemnwa pts/0    :pts/3:S.0       18:49m SCREEN -dmUS rss newsbeuter
'''
		
		self.assertEqual(monitor._check_w_output(w_output), True)

class TestLoggedInUsersMonitorRemoteSomeIdle(unittest.TestCase):
	def runTest(self):
		monitor = LoggedInUsersMonitor(3600) # 1 hour
		
		w_output = '''
solemnwa pts/2    172.24.128.21    44:29  screen -dUx i
solemnwa pts/1    :pts/2:S.0       44:29  irssi
solemnwa pts/3    172.24.128.21    18:49m screen -dUx r
solemnwa pts/0    :pts/3:S.0       18:49m SCREEN -dmUS rss newsbeuter
'''
		
		self.assertEqual(monitor._check_w_output(w_output), True)

class TestLoggedInUsersMonitorRemoteAllIdle(unittest.TestCase):
	def runTest(self):
		monitor = LoggedInUsersMonitor(60) # 1 minute
		
		w_output = '''
solemnwa pts/2    172.24.128.21    44:29  screen -dUx i
solemnwa pts/1    :pts/2:S.0       44:29  irssi
solemnwa pts/3    172.24.128.21    18:49m screen -dUx r
solemnwa pts/0    :pts/3:S.0       18:49m SCREEN -dmUS rss newsbeuter
'''
		
		self.assertEqual(monitor._check_w_output(w_output), False)

if __name__ == '__main__':
	unittest.main()
