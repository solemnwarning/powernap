#    powernapd plugin - Monitors a UDP socket for data
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

import time, socket, os, re, struct, traceback, errno
from logging import error, debug, info, warn

def get_local_macs():
    mac_addrs = []
    #Using all network devices, it is also possible to define a specific one like eth for all devices starting with eth*
    prefix = re.compile("")
    dirs = os.listdir("/sys/class/net")
    for iface in dirs:
        # Obtain MAC address
        f = open(("/sys/class/net/%s/address" % iface), 'r')
        mac = f.read()
        f.close

        nonhex = re.compile('[^0-9a-fA-F]')
        mac = nonhex.sub('', mac)

        if len(mac) == 12:
            mac_addrs.append(bytes.fromhex(mac))

    return mac_addrs

def wol_for_mac(mac):
    return bytes.fromhex("FFFFFFFFFFFF") + (mac * 16)

# Monitor plugin
#   listen for WoL data in a UDP socket. It compares if the data is specifically
#   for any of the interfaces
class WoLMonitor:

    # Initialise
    def __init__ ( self, port ):
        self._type = "wol"
        self._port = port
        self._host = '' # Bind to all Interfaces
        self._absent_seconds = 0
        self._sock = None

        mac_addrs = get_local_macs()
        self._wol_payloads = list(map(wol_for_mac, mac_addrs))

    def start ( self ):
      try:
          self._sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
          self._sock.bind(('', self._port))
          self._sock.setblocking(False)

      except Exception as e:
          error("Error setting up socket on UDP port %d: %s" % (self._port, str(e)))
          self._sock = None

    def stop(self):
        pass

    def active(self):
        active = False

        if self._sock != None:
            # Arbitrary cap on the number of packets to handle per tick, so
            # we won't spin processing packets forever.

            for x in range(128):
                packet = None
                remote_addr = None

                try:
                    # Wait for data
                    packet, remote_addr = self._sock.recvfrom(1024)

                except OSError as e:
                    if e.errno != errno.EAGAIN:
                        error("Read error on UDP port %d: %s", (self._port, str(e)));

                    break

                for wol_payload in self._wol_payloads:
                    if wol_payload in packet:
                        active = True

        return active
