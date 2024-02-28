#    powernapd plugin - Monitors a UDP socket for data
#
#    Copyright (C) 2011 Canonical Ltd.
#
#    Authors: Dustin Kirkland <kirkland@canonical.com>
#             Adam Sutton <dev@adamsutton.me.uk>
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

import errno
import os
import re
import socket
import time

from logging import error, debug, info, warn

# Obtain a list of available eth's, with its MAC address and WoL data.
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

# Monitor plugin
#   listen for data on a UDP socket (typically WOL packets)
class PowerWakeMonitor:
    # Initialise
    def __init__ ( self, port ):
        self._type = "powerwake"
        self._port = port
        self._absent_seconds = 0
        self._pending_requests = []
        self._sock = None

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

                # See if the packet is a valid PowerWake WOL request
                if (len(packet) < 114
                    or packet[0:8] != bytes("PWERWAKE", "ascii")
                    or packet[12:18] != bytes.fromhex("FFFFFFFFFFFF")):
                    # Malformed packet
                    continue

                # In some cases, powerwake wants to get a response from powernapd without
                # knowing what our MAC is (i.e. after waking us via IPMI), so we always respond
                # to this specifically malformed WoL packet.

                NOT_A_WOL_PACKET = bytes(map(ord, "Not really a WoL packet."))

                if not (packet[18:42] == NOT_A_WOL_PACKET
                    and packet[42:66] == NOT_A_WOL_PACKET
                    and packet[66:90] == NOT_A_WOL_PACKET
                    and packet[90:114] == NOT_A_WOL_PACKET):

                    wol_addrs_match = True
                    for i in range(15): # i = 0 .. 15
                        ia = 18 + (i * 6)
                        ib = ia + 6

                        if packet[ia:(ia + 6)] != packet[ib:(ib + 6)]:
                            wol_addrs_match = False
                            break

                    if not wol_addrs_match:
                        # Malformed packet
                        continue

                    if not packet[18:24] in local_macs:
                        # Not one of our MAC addresses
                        continue

                nonce = int.from_bytes(packet[8:12], byteorder='little', signed=False)

                # Reply to powerwake so it knows the machine is up.
                reply = bytes("PWERWAKF", "ascii") + nonce.to_bytes(length=4, byteorder='little', signed=False)
                self._sock.sendto(reply, remote_addr)

                active = True

        return active
