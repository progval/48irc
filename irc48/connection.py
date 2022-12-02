##
# Copyright (C) 2022  Valentin Lorentz
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License version 3,
# as published by the Free Software Foundation.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.
##

from __future__ import annotations

import io
import socket
import ssl

from . import message


class Connection:
    _raw_socket: socket.socket
    _socket: socket.socket | ssl.SSLSocket

    def __init__(self, hostname: str, port: int | str, tls: bool):
        self._raw_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self._raw_socket.connect((hostname, int(port)))

        if tls:
            context = ssl.create_default_context()
            self._socket = context.wrap_socket(
                self._raw_socket, server_hostname=hostname
            )
        else:
            self._socket = self._raw_socket

        self._buffer = b""

    def send_message(self, message: message.Message) -> None:
        self._socket.sendall(message.to_bytes())

    def get_message(self) -> message.Message:
        """Blocking"""
        line = b""

        while True:
            if b"\n" in self._buffer:
                # \r or \r\n line delimiter
                (line, self._buffer) = self._buffer.split(b"\n")
                line = line.strip(b"\r\n")
            elif b"\r" in self._buffer:
                # Server used a \r delimiter only, bad. (or we just happened to recv()
                # up until the last char; we'll dismiss the \n in the next call)
                (line, self._buffer) = self._buffer.split(b"\n")
                line = line.strip(b"\r\n")

            if line:
                return message.Message.from_bytes(line)

            self._buffer += self._socket.recv(4096)
