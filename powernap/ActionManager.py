#    powernapd action dispatcher
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

import os
import subprocess

class ActionManager:
    def __init__(self, actions, actions_path):
        self.actions = []
        self.actions_path = actions_path
        self.last_activity = 0

        for action in actions:
            self.actions.append({
                "name":  action["name"],
                "after": action["after"],
                "warn":  (action["warn"] if "warn" in action else None),

                "triggered": False,
                "warned": False,
            })

    def update(self, active, timestamp):
        if active:
            self.last_activity = timestamp

        if timestamp < self.last_activity:
            # timestamp went backwards, wtf?
            self.last_activity = timestamp

        for action in self.actions:
            trigger_in = action["after"] - (timestamp - self.last_activity)

            if action["warn"] != None:
                warn_in = trigger_in - action["warn"]

                if warn_in <= 0 and trigger_in > 0 and not action["warned"]:
                    self.issue_warning(action["name"], trigger_in)
                    action["warned"] = True

                if warn_in > 0 and action["warned"]:
                    self.rescind_warning(action["name"])
                    action["warned"] = False

            if trigger_in <= 0 and not action["triggered"]:
                self.exec_action(action["name"], "true")
                action["triggered"] = True

            if trigger_in > 0 and action["triggered"]:
                self.exec_action(action["name"], "false")
                action["triggered"] = False
                action["warned"] = False

    def issue_warning(self, action_name, time_remain_secs):
        msg = f"powernapd will perform the {action_name} action in {time_remain_secs} due to system inactivity"
        subprocess.run("wall", stdin = msg, text = True)

    def rescind_warning(self, action_name):
        msg = f"powernapd will no longer perform the {action_name} action in due to system activity"
        subprocess.run("wall", stdin = msg, text = True)

    def exec_action(self, action_name, param):
        action_env = os.environ.copy()
        action_env["POWERNAPD_PID"] = str(os.getpid())

        subprocess.run([ self.actions_path + "/" + action_name, param ], stdin = subprocess.DEVNULL, env = action_env)
