#    powernapd plugin - Monitors logged in users
#    Copyright (C) 2023 Daniel Collins <solemnwarning@solemnwarning.net>
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

import logging
import pytimeparse
import subprocess

class LoggedInUsersMonitor:
    def __init__(self, max_idle_secs):
        self._type = "users"
        self._max_idle_secs = max_idle_secs

    def start(self):
        pass

    def stop(self):
        pass

    def active(self):
        result = subprocess.run(["w", "--no-header", "--short"],
            capture_output = True, text = True, stdin = subprocess.DEVNULL)

        if result.returncode == 0:
            return self._check_w_output(result.stdout)

        else:
            logging.error(f"LoggedInUsersMonitor 'w' command failed with status {result.returncode}")
            logging.error(result.stderr)

            return False

    def _check_w_output(self, output):
        lines = output.split("\n")

        for line in lines:
            if line == "":
                continue

            logging.debug("LoggedInUsersMonitor processing line: " + line)

            [ user, tty, host, idle_time, what ] = line.split(None, 4)
            idle_secs = pytimeparse.parse(idle_time)

            logging.debug(f"LoggedInUsersMonitor idle_secs is {idle_secs}")

            if idle_secs != None and (self._max_idle_secs == None or idle_secs <= self._max_idle_secs):
                return True

        return False
