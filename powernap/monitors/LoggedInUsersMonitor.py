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
import re
import subprocess

class LoggedInUsersMonitor:
    DAYS_REGEX = re.compile(r"(\d+)days")
    HOURS_MINUTES_REGEX = re.compile(r"(\d+):(\d+)m")
    MINUTES_SECONDS_REGEX = re.compile(r"(\d+):(\d+)")
    SECONDS_REGEX = re.compile(r"(\d+)\.\d+s")

    def __init__(self, max_idle_secs):
        self._type = "users"
        self._max_idle_secs = max_idle_secs

    def start(self):
        pass

    def stop(self):
        pass

    def active(self):
        # Ensure w output isn't localised
        w_env = os.environ.copy()
        w_env["LC_ALL"] = "C"

        result = subprocess.run(["w", "--no-header", "--short"],
            capture_output = True, text = True, stdin = subprocess.DEVNULL, env = w_env)

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
            idle_secs = None

            # Idle time parsing based on format in procps 4.0.2

            days_match            = LoggedInUsersMonitor.DAYS_REGEX           .fullmatch(idle_time)
            hours_minutes_match   = LoggedInUsersMonitor.HOURS_MINUTES_REGEX  .fullmatch(idle_time)
            minutes_seconds_match = LoggedInUsersMonitor.MINUTES_SECONDS_REGEX.fullmatch(idle_time)
            seconds_match         = LoggedInUsersMonitor.SECONDS_REGEX        .fullmatch(idle_time)

            if days_match:
                idle_days = int(days_match.group(1))
                idle_secs = idle_days * 24 * 60 * 60

            elif hours_minutes_match:
                idle_hours = int(hours_minutes_match.group(1))
                idle_minutes = int(hours_minutes_match.group(2))
                idle_secs = (idle_hours * 60 * 60) + (idle_minutes * 60)

            elif minutes_seconds_match:
                idle_minutes = int(minutes_seconds_match.group(1))
                idle_secs = int(minutes_seconds_match.group(2))
                idle_secs = (idle_minutes * 60) + idle_secs

            elif seconds_match:
                idle_secs = int(seconds_match.group(1))

            logging.debug(f"LoggedInUsersMonitor idle_secs is {idle_secs}")

            if idle_secs != None and (self._max_idle_secs == None or idle_secs <= self._max_idle_secs):
                return True

        return False
