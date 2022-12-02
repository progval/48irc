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

import collections
import dataclasses
import typing

from .message import Message
from .incoming import IncomingHandler
from .outgoing import OutgoingHandler

if typing.TYPE_CHECKING:
    from .connection import Connection
    from .ui import UI

BUFFER_SIZE = 100


@dataclasses.dataclass
class BufferMessage:
    author: str | None
    content: str
    prefix: str = ""


class State:
    _connection: Connection
    _messages: collections.deque[BufferMessage]
    _ui: UI

    def __init__(self, default_nick: str):
        self.shut_down = False
        self.default_nick = default_nick
        self.nick_attempt_count = 0
        self._messages = collections.deque(maxlen=BUFFER_SIZE)
        self._incoming_handler = IncomingHandler(self)
        self._outgoing_handler = OutgoingHandler(self)

    def attach_connection(self, connection: Connection) -> None:
        self._connection = connection
        self.send_message_with_echo("NICK", [self.default_nick])
        self.send_message_with_echo(
            "USER", [self.default_nick, "0", "*", self.default_nick]
        )

    def attach_ui(self, ui: UI) -> None:
        self._ui = ui

    def on_incoming_message(self, msg: Message) -> None:
        if msg.command.isnumeric():
            buf_msg = BufferMessage(
                author=None,
                content=f"{msg.command} {' '.join(msg.params[1:])}",
                prefix="-->",
            )
        else:
            buf_msg = BufferMessage(
                author=msg.source,
                content=f"{msg.command} {' '.join(msg.params)}",
                prefix="-->",
            )
        self.display(buf_msg)
        self._incoming_handler(msg)

    def display(self, buf_msg: BufferMessage) -> None:
        self._ui.display_message(buf_msg)
        self._messages.append(buf_msg)

    def send_message_with_echo(self, command: str, params: list[str]):
        buf_msg = BufferMessage(
            author=None, content=f"{command} {' '.join(params)}", prefix="<--"
        )
        self._ui.display_message(buf_msg)
        self._messages.append(buf_msg)
        self.send_message(command, params)

    def send_message(self, command: str, params: list[str]):
        self._connection.send_message(Message(command, params))

    def on_user_input(self, s: str) -> None:
        if not s:
            return
        if s.startswith("/"):
            if " " in s:
                (command, args) = s[1:].split(" ", 1)
            else:
                command = s[1:]
                args = ""
            self._outgoing_handler(command, args)
