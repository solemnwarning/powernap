#!/usr/bin/python3
#
#    powerwake.py - handles powerwaked config and initializes Monitors.
#
#    Copyright (C) 2011 Canonical Ltd.
#
#    Authors: Andres Rodriguez <andreserl@canonical.com>
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

import configparser, sys, re, os, logging
from .monitors import ARPMonitor

class PowerWake:

    def __init__(self, config_filename):
        self.PKG = "powerwake"
        self.DEBUG = False
        self.LOG = ""
        self.MONITORS = []
        # Load default config file (/etc/powernap/config)
        self.load_config_file(config_filename)

    def load_config_file(self, config_filename):
        cfg = configparser.ConfigParser()
        cfg.read(config_filename)

        arp_monitor = {}

        for section_name in cfg.sections():
            # [powerwake]
            # debug = yes
            # log = /var/log/powerwaked.log
            if section_name == "powerwake":
                for (name, value) in cfg.items(section_name):
                    if name == "debug":
                        self.DEBUG = (value == "y" or value == "yes")
                    elif name == "log":
                        self.LOG = value
                    else:
                        raise Exception("Unexpected value '" + name + "' in [" + self.PKG + "] section in " + config_filename)

            # [ARPMonitor]
            # file = /etc/powernap/powerwaked.ARPMonitor.ethers
            # a.b.c.d = aa:bb:cc:dd:ee:ff
            elif section_name == "ARPMonitor":
                for (name, value) in cfg.items(section_name):
                    if name == "file":
                        file_ip_to_mac = self.get_monitored_hosts(value)
                        for (ip, mac) in file_ip_to_mac.items():
                            arp_monitor[ip] = self.normalise_mac(mac)
                    elif self.is_ip(name):
                        if self.is_mac(value):
                            arp_monitor[name] = self.normalise_mac(value)
                        else:
                            raise Exception("Unexpected value '" + value + "' in [ARPMonitor] section (expected a MAC address) in " + config_filename)
                    else:
                        raise Exception("Unexpected value '" + name + "' in [ARPMonitor] section (expected 'file' or an IP address) in " + config_filename)
            else:
                raise Exception("Unexpected [" + section_name + "] section in " + config_filename)

        if arp_monitor:
            self.MONITORS.append({"monitor":"ARPMonitor", "cache":arp_monitor})

    def get_monitors(self):
        monitor = []
        for config in self.MONITORS:
            if config["monitor"] == "ARPMonitor":
                p = ARPMonitor.ARPMonitor(config)
            monitor.append(p)

        return monitor

    def get_monitored_hosts(self, filename):
        host_to_mac = {}
        if os.path.exists(filename):
            f = open(filename, 'r')
            for i in f.readlines():
                (m, h) = i.split()
                host_to_mac[h] = m
            f.close()
        return host_to_mac

    def set_monitored_hosts(self, host_to_mac, filename):
        f = open(filename, 'w')
        for h in host_to_mac:
            if self.is_mac(host_to_mac[h]):
                f.write("%s %s\n" % (host_to_mac[h], h))
        f.close()

    def get_mac_or_ip_from_arp(self, host):
        mac_or_ip = None
        for i in os.popen("/usr/sbin/arp -n"):
            m = i.split()[2]
            h = i.split()[0]
            if self.is_mac(host) and host == m and self.is_ip(h):
                mac_or_ip = h
                break
            if self.is_ip(host) and host == h and self.is_mac(m):
                mac_or_ip = m
                break
        #if not mac_or_ip:
        #    raise BaseException("Error")
        return mac_or_ip

    def is_ip(self, ip):
        r1 = re.compile('^[0-9]+\.[0-9]+\.[0-9]+\.[0-9]+$')
        if r1.match(ip):
            return True
        else:
            return False

    def is_mac(self, mac):
        r1 = re.compile('^[0-9a-fA-F]{12}$')
        r2 = re.compile('^[0-9a-fA-F]{2}:[0-9a-fA-F]{2}:[0-9a-fA-F]{2}:[0-9a-fA-F]{2}:[0-9a-fA-F]{2}:[0-9a-fA-F]{2}$')
        if r1.match(mac) or r2.match(mac):
            return 1
        else:
            return 0

    def normalise_mac(self, mac):
        return mac.replace(":", "").lower()

#### --------------------------------- from powerwake --------------------------------####

    # Source the cached, known arp entries
    def get_arp_cache(self):
        host_to_mac = {}
        #for file in ["/var/cache/%s/ethers" % self.PKG, "/etc/ethers", "%s/.cache/ethers" % HOME]:
        for file in ["/var/cache/%s/ethers" % self.PKG, "/etc/ethers"]:
            if os.path.exists(file):
                f = open(file, 'r')
                for i in f.readlines():
                    try:
                        (m, h) = i.split()
                        host_to_mac[h] = m
                    except:
                        pass
                f.close()
        return host_to_mac

    # Source the current, working arp table
    def get_arp_current(self, host_to_mac):
        # Load hostnames
        for i in os.popen("/usr/sbin/arp"):
            m = i.split()[2]
            h = i.split()[0]
            if is_mac(m):
                host_to_mac[h] = m
        # Load ip addresses
        for i in os.popen("/usr/sbin/arp -n"):
            m = i.split()[2]
            h = i.split()[0]
            if is_mac(m):
                host_to_mac[h] = m
        return host_to_mac

    def write_arp_cache(self, host_to_mac):
        if not os.access("%s/.cache/" % HOME, os.W_OK):
            return
        if not os.path.exists("%s/.cache/" % HOME):
            os.makedirs("%s/.cache/" % HOME)
        f = open("%s/.cache/ethers" % HOME, 'a')
        f.close()
        for file in ["/var/cache/%s/ethers" % PKG, "%s/.cache/ethers" % HOME]:
            if os.access(file, os.W_OK):
                f = open(file, 'w')
                for h in host_to_mac:
                    if self.is_mac(host_to_mac[h]):
                        f.write("%s %s\n" % (host_to_mac[h], h))
                f.close()
