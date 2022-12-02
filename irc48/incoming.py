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
        else:
            self._passthrough(msg)

    def _passthrough(self, msg: Message) -> None:
        if msg.command.isnumeric():
            author = None
        else:
            author = msg.source
        (buf_name, params) = msg.pop_channel(self._state)

        from .state import BufferMessage

        buf_msg = BufferMessage(
            author=None,
            content=f"{msg.command} {' '.join(params)}",
            prefix="-->",
        )
        self._state.display(buf_name, buf_msg)

    def onPing(self, msg: Message) -> None:
        self._state.send_message("PONG", [msg.params[-1]])

    def on433(self, msg: Message) -> None:
        """ERR_NICKNAMEINUSE"""
        self._passthrough(msg)
        self._state.nick_attempt_count += 1
        self._state.current_nick = (
            f"{self._state.default_nick}{self._state.nick_attempt_count}"
        )
        self._state.send_message_with_echo("NICK", [self._state.current_nick])

    def onJoin(self, msg: Message) -> None:
        if msg.source and msg.source.split("!")[0] == self._state.current_nick:
            # we just joined a channel, switch to that buffer
            self._state.switch_to_buffer(msg.params[0])
        self._passthrough(msg)

    def onPrivmsg(self, msg: Message) -> None:
        from .state import BufferMessage

        author = msg.source and msg.source.split("!")[0]
        buf_msg = BufferMessage(
            author=author,
            content=msg.params[1],
        )

        target = msg.params[0]
        if target.lower() == self._state.current_nick.lower():
            # It's a private message
            assert author
            target = author

        self._state.display(target, buf_msg)
