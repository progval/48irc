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

import atexit
import dataclasses
import io
import os
import queue
import readline
import select
import sys
import termios
import time
import tty
import typing

from . import formatting

if typing.TYPE_CHECKING:
    from .state import State, BufferMessage


class _ControlMessage:
    pass


@dataclasses.dataclass
class SwitchToBuffer(_ControlMessage):
    buf_name: str | None


class UI:
    def __init__(self, state: State):
        self._state = state
        self._display_queue: queue.Queue[
            BufferMessage | _ControlMessage
        ] = queue.Queue()

    def start(self) -> None:
        pass

    def loop_input(self) -> None:
        while not self._state.shut_down:
            if select.select([sys.stdin], [], [], 0.1)[0]:
                line = sys.stdin.readline().rstrip("\n")
                self._state.on_user_input(line)

    def loop_display(self) -> None:
        while not self._state.shut_down:
            try:
                msg = self._display_queue.get(timeout=0.01)
            except queue.Empty:
                continue
            else:
                if isinstance(msg, SwitchToBuffer):
                    os.system("clear")
                    buf_name = msg.buf_name
                    for msg in self._state.messages[buf_name]:
                        self.print_message(msg)
                    self._state.current_buffer = buf_name
                else:
                    assert not isinstance(msg, _ControlMessage)
                    self.print_message(msg)

    def print_message(self, msg):
        content = formatting.irc_to_ansi(msg.content)
        if msg.author:
            if msg.action:
                print(f"\r* {msg.author} {content}")
            else:
                print(f"\r<{msg.author}> {content}")
        else:
            print(f"\r{msg.prefix} {content}")

    def display_message(self, msg: BufferMessage) -> None:
        self._display_queue.put(msg)

    def switch_to_buffer(self, buf_name: str | None) -> None:
        self._display_queue.put(SwitchToBuffer(buf_name))
