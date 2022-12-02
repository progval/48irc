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

import typing

if typing.TYPE_CHECKING:
    from .state import State, BufferMessage


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

    def onNick(self, command, nick: str) -> None:
        self._state.default_nick = nick
        self._state.nick_attempt_count = 0
        self._passthrough(command, nick)

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
