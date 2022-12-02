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

from .message import Message

if typing.TYPE_CHECKING:
    from .state import State, BufferMessage


class IncomingHandler:
    def __init__(self, state: State):
        self._state = state

    def __call__(self, msg: Message) -> None:
        method_name = "on" + msg.command.capitalize()
        method = getattr(self, method_name, None)
        if method:
            method(msg)

    def onPing(self, msg: Message) -> None:
        self._state.send_message_with_echo("PONG", [msg.params[-1]])

    def on433(self, msg: Message) -> None:
        """ERR_NICKNAMEINUSE"""
        self._state.nick_attempt_count += 1
        self._state.current_nick = (
            f"{self._state.default_nick}{self._state.nick_attempt_count}"
        )
        self._state.send_message_with_echo("NICK", [self._state.current_nick])

    def onJoin(self, msg: Message) -> None:
        if msg.source and msg.source.split("!")[0] == self._state.current_nick:
            # we just joined a channel, switch to that buffer
            self._state.current_buffer = msg.params[0]
