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
        histfile = os.path.join(os.path.expanduser("~"), ".irc48_history")
        try:
            readline.read_history_file(histfile)
            # default history len is -1 (infinite), which may grow unruly
            readline.set_history_length(1000)
        except FileNotFoundError:
            pass

        atexit.register(readline.write_history_file, histfile)

        # tty.setcbreak(sys.stdin.fileno())

    def loop_input(self) -> None:
        fd = sys.stdin.fileno()

        old_settings = termios.tcgetattr(fd)
        # stdin_wrapper = io.TextIOWrapper(sys.stdin.buffer)
        try:
            # tty.setraw(fd)
            buf = ""
            while not self._state.shut_down:
                if select.select([sys.stdin], [], [], 0.1)[0]:
                    line = sys.stdin.readline().rstrip("\n")
                    self._state.on_user_input(line)
                # self._loop_input_one(stdin_wrapper)
        finally:
            termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)

    def _loop_input_one(self, stdin_wrapper) -> None:
        assert False
        if select.select([sys.stdin.buffer], [], [], 0.1)[0]:
            text = stdin_wrapper.read(1)
            readline.insert_text(text)
            buf = readline.get_line_buffer()
            print(repr(readline.get_line_buffer()))
            if "\n" in buf:
                print("newline")
                (command, *new_buf) = buf.split("\n", 1)
                readline.insert_text("\x08" * len(buf))  # WTF; how else to clear it?
                readline.insert_text(new_buf[0])
                print(repr(command), repr(new_buf))
            readline.redisplay()

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
