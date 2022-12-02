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

import logging

import dataclasses


MAX_LINE_LENGTH = 512


COMMANDS_WITH_NO_CHANNEL = """
AUTHENTICATE PASS NICK PING PONG OPER QUIT ERROR
LIST
MOTD VERSION ADMIN CONNECT LUSERS TIME STATS HELP INFO
WHOIS WHOWAS
KILL REHASH RESTART SQUIT
AWAY LINKS USERHOST WALLOPS
""".split()

COMMANDS_WITH_CHANNEL = "JOIN PART TOPIC NAMES KICK".split()

COMMANDS_WITH_NICK_OR_CHANNEL = "MODE PRIVMSG NOTICE".split()


@dataclasses.dataclass
class Message:
    command: str
    params: list[str]
    source: str | None = None

    @classmethod
    def from_string(cls, s: str) -> Message:
        for char in "\0\r\n":
            assert char not in s, f"{char!r} in {s!r}"
        first_tokens, *trailing = s.split(" :", 1)
        tokens = [*first_tokens.split(" "), *trailing]

        source = tokens.pop(0)[1:] if tokens[0].startswith(":") else None
        (command, *params) = tokens

        return Message(source=source, command=command, params=params)

    @classmethod
    def from_bytes(cls, b: bytes) -> Message:
        return cls.from_string(b.decode(errors="ignore"))

    def to_bytes(self) -> bytes:
        if self.source:
            source = f":{self.source} "
        else:
            source = ""

        assert " " not in self.command, "Space in {command!r}"

        if not self.params:
            return f"{source}{self.command}\r\n".encode()

        (*params, trailing) = self.params

        for param in params:
            assert " " not in param, "Space in {param!r}"

        b = f"{source}{self.command.upper()} {' '.join(params)} :{trailing}".encode()

        if len(b) > MAX_LINE_LENGTH:
            logging.warning("Line too long: %r", b)
            b = b[0:510]

        return b + b"\r\n"

    def pop_channel(self, state) -> tuple[str | None, list[str]]:
        if len(self.params) == 0:
            return (None, [])
        command = self.command.upper()
        if command.isnumeric():
            if len(self.params) >= 2 and state.is_channel(self.params[1]):
                return (self.params[1], self.params[2:])
            else:
                return (None, self.params)
        elif command in COMMANDS_WITH_NICK_OR_CHANNEL:
            if len(self.params) >= 1 and state.is_channel(self.params[0]):
                return (self.params[0], self.params[1:])
            else:
                return (None, self.params)
        elif command in COMMANDS_WITH_NO_CHANNEL:
            return (None, self.params)
        elif command == "WHO":
            # debatable
            return (None, self.params)
        elif command in COMMANDS_WITH_CHANNEL:
            return (self.params[0], self.params[1:])
        elif command == "INVITE":
            if len(self.params) >= 2:
                return (self.params[1], [self.params[0], *self.params[2:]])
            else:
                return (None, self.params)
        else:
            # Unknown command.
            return (None, self.params)
