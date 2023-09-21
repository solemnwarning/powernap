#    powernapd.conf loader
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

import pytimeparse
import re

class ParseError(Exception):
    def __init__(self, message):
        self.message = message
        super().__init__(self.message)

COMMENT = re.compile("^#");

# Splits the given string on whitespace, returning the first word and the rest of the string.
#
# _shift_word("hello world") => [ "hello", "world" ]
# _shift_word("foo bar baz") => [ "foo", "bar baz" ]
# _shift_word("foo")         => [ "foo", "" ]
# _shift_word("")            => [ "", "" ]
#
def _shift_word(words):
    return (words.split(None, 1) + ["", ""])[:2]

class ConfigReader:
    def __init__(self, valid_actions):
        self.valid_actions = valid_actions

    def read_config(self, filename):
        f = open(filename, 'r')
        lines = f.readlines()
        f.close()

        return self.parse_config(lines, filename)

    def parse_config(self, lines, filename):
        config = {
            "actions": [],
            "debug": False,
            "interval": 1,
            "log": None,
            "monitors": [],
        }

        line_num = 0
        for line in lines:
            line = line.strip()
            line_num += 1

            try:
                if COMMENT.match(line) or line == "":
                    continue

                directive, parameters = _shift_word(line)

                if directive == "monitor":
                    config["monitors"].append(self._parse_monitor(parameters))

                elif directive == "action":
                    config["actions"].append(self._parse_action(parameters))

                elif directive == "debug":
                    if parameters != "":
                        raise ParseError(f"Unexpected '{parameters}' after 'debug'")

                    config["debug"] = True

                elif directive == "log":
                    if parameters == "":
                        raise ParseError("Expected filename or 'syslog' after 'log'")

                    if config["log"] != None:
                        raise ParseError("'log' can only be specified once")

                    config["log"] = parameters

                elif directive == "interval":
                    config["interval"] = int(parameters)

                else:
                    raise ParseError(f"Unknown directive {directive}")

            except ParseError as e:
                raise Exception(f"{e.message} at {filename} line {line_num}") from None

        return config

    def _parse_monitor(self, parameters):
        monitor_type, monitor_parameters = _shift_word(parameters)

        valid_monitors = {
            "console":     self._parse_console_monitor,
            "disk":        self._parse_disk_monitor,
            "keyboard":    self._parse_keyboard_monitor,
            "load":        self._parse_load_monitor,
            "mouse":       self._parse_mouse_monitor,
            "powerwake":   self._parse_port_monitor_func("powerwake", 57748),
            "process":     self._parse_process_monitor,
            "process-io":  self._parse_process_io_monitor,
            "tcp":         self._parse_port_monitor_func("tcp", None),
            "users":       self._parse_users_monitor,
            "udp":         self._parse_port_monitor_func("udp", None),
            "wol":         self._parse_port_monitor_func("wol", None),
        }

        if monitor_type in valid_monitors:
            return valid_monitors[monitor_type](monitor_parameters)
        else:
            raise ParseError(f"Unknown monitor type {monitor_type}")

    def _parse_console_monitor(self, monitor_parameters):
        if monitor_parameters != "":
            raise ParseError(f"Unexpected '{monitor_parameters}' after 'console'")

        return { "type": "console" }

    def _parse_disk_monitor(self, monitor_parameters):
        if monitor_parameters == "":
            raise ParseError(f"Expected device name after 'disk'")

        return { "type": "disk", "device": monitor_parameters }

    def _parse_keyboard_monitor(self, monitor_parameters):
        if monitor_parameters != "":
            raise ParseError(f"Unexpected '{monitor_parameters}' after 'keyboard'")

        return { "type": "keyboard" }

    def _parse_mouse_monitor(self, monitor_parameters):
        if monitor_parameters != "":
            raise ParseError(f"Unexpected '{monitor_parameters}' after 'mouse'")

        return { "type": "mouse" }

    def _parse_load_monitor(self, monitor_parameters):
        m = re.compile("^\\d+(\\.\\d+)?$").match(monitor_parameters)

        if m:
            load = float(monitor_parameters)
            return { "type": "load", "threshold": load }
        elif monitor_parameters == "n":
            return { "type": "load", "threshold": "n" }

        else:
            raise ParseError(f"Expected number after 'load'")

    def _parse_process_monitor(self, monitor_parameters):
        if monitor_parameters == "":
            raise ParseError(f"Expected a regular expression after 'process'")

        proc_re = None
        try:
            proc_re = re.compile(monitor_parameters)
        except re.error as e:
            raise ParseError(f"Invalid regular expression after 'process': {e}")

        return { "type": "process", "regex": proc_re }

    def _parse_process_io_monitor(self, monitor_parameters):
        if monitor_parameters == "":
            raise ParseError(f"Expected a regular expression after 'process-io'")

        proc_re = None
        try:
            proc_re = re.compile(monitor_parameters)
        except re.error as e:
            raise ParseError(f"Invalid regular expression after 'process-io': {e}")

        return { "type": "process-io", "regex": proc_re }

    def _parse_users_monitor(self, monitor_parameters):
        next_word, monitor_parameters = _shift_word(monitor_parameters)

        max_idle_secs = None

        if next_word == "":
            pass

        elif next_word == "max-idle":
            [ max_idle_t, monitor_parameters ] = _shift_word(monitor_parameters)
            max_idle_secs = self._parse_time_duration(max_idle_t, "max-idle")

            if monitor_parameters != "":
                raise ParseError(f"Unexpected '{monitor_parameters}' after '{max_idle_t}'")

        else:
            raise ParseError(f"Unexpected '{next_word}' after 'users'")

        return { "type": "users", "max_idle_secs": max_idle_secs }

    def _parse_port_monitor_func(self, monitor_type, default_port):
        def func(monitor_parameters):
            m = re.compile("^port (\\d+)$").match(monitor_parameters)

            if m:
                port = int(m.group(1))

                if port > 65535:
                    raise ParseError(f"Invalid port number {port}")

                return { "type": monitor_type, "port": port }
            elif monitor_parameters == "" and default_port != None:
                return { "type": monitor_type, "port": 57748 }
            else:
                raise ParseError(f"Expected 'port <port number>' after '{monitor_type}'")

        return func

    def _parse_action(self, parameters):
        action_name, parameters = _shift_word(parameters)

        if not action_name in self.valid_actions:
            raise ParseError(f"Unknown action {action_name}")

        action = {
            "name": action_name,
        }

        while parameters != "":
            x, parameters = _shift_word(parameters)

            if x == "after":
                d, parameters = _shift_word(parameters)

                if "after" in action:
                    raise ParseError(f"Duplicate after options for action {action_name}")

                action["after"] = self._parse_time_duration(d, "after")

            elif x == "warn":
                d, parameters = _shift_word(parameters)

                if "warn" in action:
                    raise ParseError(f"Duplicate warn options for action {action_name}")

                action["warn"] = self._parse_time_duration(d, "warn")

            else:
                raise ParseError(f"Unknown option {x} for action {action_name}")

        if not "after" in action:
            raise ParseError(f"No after option specified for action {action_name}")

        return action

    def _parse_time_duration(self, d, preceeded_by):
        if d == "":
            raise ParseError(f"Expected a time duration (e.g. 1m) after '{preceeded_by}'")

        duration = pytimeparse.parse(d)

        if duration == None:
            raise ParseError(f"Unable to parse time duration {d} after '{preceeded_by}'")

        return duration
