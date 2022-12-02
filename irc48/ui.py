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

if typing.TYPE_CHECKING:
    from .state import State, BufferMessage


class UI:
    def __init__(self, state: State):
        self._state = state
        self._display_queue: queue.Queue[BufferMessage] = queue.Queue()

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
                msg = self._display_queue.get(timeout=0.1)
            except queue.Empty:
                continue
            else:
                if msg.author:
                    print(f"\r<{msg.author}> {msg.content}")
                else:
                    print(f"\r{msg.prefix} {msg.content}")
                readline.redisplay()

    def display_message(self, msg: BufferMessage):
        self._display_queue.put(msg)
