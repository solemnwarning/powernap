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

import time, errno
from logging import error, debug, info, warn

# Monitor plugin
#   listen for data on a UDP socket (typically WOL packets)
class UDPMonitor:

    # Initialise
    def __init__ ( self, port ):
        self._type = "udp"
        self._port = port
        self._absent_seconds = 0
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

                active = True

        return active
