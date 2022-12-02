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
                content=" ".join(msg.params),
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

    def send_message_with_echo(self, command, params):
        buf_msg = BufferMessage(
            author=None, content=f"{command} {' '.join(params)}", prefix="<--"
        )
        self._ui.display_message(buf_msg)
        self._messages.append(buf_msg)

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


class IncomingHandler:
    def __init__(self, state: State):
        self._state = state

    def __call__(self, msg: Message):
        method_name = "on" + msg.command.capitalize()
        method = getattr(self, method_name, None)
        if method:
            method(msg)

    def onPing(self, msg: Message):
        self._state.send_message_with_echo("PONG", [msg.params[-1]])


class OutgoingHandler:
    def __init__(self, state: State):
        self._state = state

    def __call__(self, command: str, args: str):
        method_name = "on" + command.capitalize()
        method = getattr(self, method_name, None)
        if method:
            method(command, args)
        else:
            self._passthrough(command, args)

    def _passthrough(self, command: str, args: str) -> None:
        self._state.send_message_with_echo(command.upper(), args.split())

    def onQuit(self, command, reason: str) -> None:
        self._passthrough(command, reason)
        self._state.shut_down = True

    def onMsg(self, command: str, args: str) -> None:
        command = command.upper()
        if command == "MSG":
            command = "PRIVMSG"
        (target, content) = args.split(maxsplit=1)
        self._state.send_message_with_echo(command, [target, content])

    onPrivmsg = onNotice = onMsg
