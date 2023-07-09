#    powernapd plugin - Monitors process table for presence of process
#
#    Copyright (C) 2011 Canonical Ltd.
#
#    Authors: Dustin Kirkland <kirkland@canonical.com>
#             Andres Rodriguez <andreserl@canonical.com>
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

import os, re, subprocess, time
from logging import error, debug, info, warn
from pathlib import(Path)

# Check /dev/*, such that we don't powernap the system if someone
# is actively using a terminal device
def get_console_activity():
    ptmx = "/dev/ptmx"
    time = os.stat(ptmx).st_mtime
    irqs = get_interrupts()
    return time, irqs

# Obtain the interrupts at any given point in time
def get_interrupts():
    interrupts = 0
    for irq in os.listdir("/sys/kernel/irq/"):
        source = Path("/sys/kernel/irq/" + irq + "/actions").read_text()
        if source == "i8042" or source == "keyboard" or source == "mouse":
            counts = Path("/sys/kernel/irq/" + irq + "/per_cpu_count").read_text().split(",")
            for i in counts:
                interrupts += int(i)
    return interrupts

class ConsoleMonitor():

    # Initialise
    def __init__(self, config):
        self._type = config['monitor']
        self._name = config['name']
        self._absent_seconds = 0
        self._time, self._irqs = get_console_activity()

    # Check for PIDs
    def active(self):
        cur_time, cur_irqs = get_console_activity()
        if cur_time > self._time or cur_irqs > self._irqs:
                self._irqs = cur_irqs
                self._time = cur_time
                return True
        return False

    def start(self):
        pass

