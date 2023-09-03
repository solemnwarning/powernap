#!/usr/bin/python3
#
#    powernap.py - handles powernap's config and initializes Monitors.
#
#    Copyright (C) 2010 Canonical Ltd.
#
#    Authors: Andres Rodriguez <andreserl@ubuntu.com>
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

import sys, re, os
from .monitors import ProcessMonitor, LoadMonitor, InputMonitor, TCPMonitor, UDPMonitor, IOMonitor, WoLMonitor, ConsoleMonitor, DiskMonitor, PowerWakeMonitor
from ConfigReader import ConfigReader

class PowerNap:

    def __init__(self):
        self.PKG = "powernap"
        self.CONFIG_FILE = "/etc/powernap/config"

        # Load names of scripts from /etc/powernap/actions/
        self.actions = self.enum_actions()
        # Load default config file (/etc/powernap/config)
        self.load_config_file()

        self.INTERVAL_SECONDS = self.config["interval"]
        self.DEBUG = self.config["debug"]
        self.LOG = self.config["log"]

    def enum_actions(self):
        return os.listdir("/etc/powernap/actions/")

    def load_config_file(self):
        cr = ConfigReader(self.actions)
        self.config = cr.read_config(self.CONFIG_FILE)

    def get_monitors(self):
        monitor = []
        for config in self.config["monitors"]:
            if config["type"] == "console":     p = ConsoleMonitor.ConsoleMonitor()
            if config["type"] == "disk":        p = DiskMonitor.DiskMonitor(config["device"])
            if config["type"] == "keyboard":    p = InputMonitor.InputMonitor("kbd")
            if config["type"] == "load":        p = LoadMonitor.LoadMonitor(config["threshold"])
            if config["type"] == "mouse":       p = InputMonitor.InputMonitor("mice")
            if config["type"] == "process":     p = ProcessMonitor.ProcessMonitor(config["regex"])
            if config["type"] == "process-io":  p = IOMonitor.IOMonitor(config["regex"])
            if config["type"] == "powerwake":   p = PowerWakeMonitor.PowerWakeMonitor(config["port"])
            if config["type"] == "tcp":         p = TCPMonitor.TCPMonitor(config["port"], config["port"])
            if config["type"] == "udp":         p = UDPMonitor.UDPMonitor(config["port"])
            if config["type"] == "wol":         p = WoLMonitor.WoLMonitor(config["port"])

            monitor.append(p)

        return monitor
