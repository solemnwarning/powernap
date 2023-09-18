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

import os
import re
import socket
import time
import threading

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
class PowerWakeMonitor (threading.Thread):
    # Initialise
    def __init__ ( self, port ):
        threading.Thread.__init__(self)
        self._type = "powerwake"
        self._port = port
        self._running = False
        self._absent_seconds = 0
        self._pending_requests = []

        # Create socket
        self._sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

    # Start thread
    def start ( self ):
      self._running = True
      threading.Thread.start(self)

    # Stop thread
    def stop ( self ): self._running = False

    # Open port and wait for data (any data will trigger the monitor)
    def run ( self ):
        listen = False

        local_macs = get_local_macs()

        while self._running:
            if not listen:
                try:
                    debug('%s - configure socket' % self)
                    self._sock.bind(('', self._port))
                    self._sock.settimeout(1.0)
                    listen = True
                except Exception as e:
                    error('%s - failed to config socket [e=%s]' % (self, str(e)))
                    time.sleep(1.0)
            else:
                try:
                    # Wait for data
                    packet, remote_addr = self._sock.recvfrom(1024)

                    # See if the packet is a valid PowerWake WOL request
                    if (len(packet) < 114
                        or packet[0:8] != bytes("PWERWAKE", "ascii")
                        or packet[12:18] != bytes.fromhex("FFFFFFFFFFFF")):
                        # Malformed packet
                        continue

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

                    # The packet is valid, so we store it and send a response from the main thread
                    # on the next tick, this ensures we don't falsely send a response to powerwake
                    # before initiating a shutdown.

                    nonce = int.from_bytes(packet[8:12], byteorder='little', signed=False)

                    self._pending_requests.append([ remote_addr, nonce ])
                    debug('%s - data packet received' % self)
                    self.reset()

                except:
                    pass # timeout

    def active(self):
        if self._pending_requests:
            # Acknowledge any pending powerwake requests
            while self._pending_requests:
                remote_addr, nonce = self._pending_requests.pop()

                packet = bytes("PWERWAKF", "ascii") + nonce.to_bytes(length=4, byteorder='little', signed=False)
                self._sock.sendto(packet, remote_addr)

            return True

        return False
