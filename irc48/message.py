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

import dataclasses


@dataclasses.dataclass
class Message:
    source: str | None
    command: str
    params: list[str]

    @classmethod
    def from_string(cls, s: str) -> Message:
        for char in "\0\r\n":
            assert char not in s, f"{char!r} in {s!r}"
        first_tokens, *trailing = s.split(" :", 1)
        tokens = [*first_tokens.split(" "), *trailing]

        source = tokens.pop(0)[1:] if tokens[0].startswith(":") else None
        (command, *params) = tokens

        return Message(source=source, command=command, params=params)

    def to_string(self) -> str:
        if self.source:
            source = f":{self.source} "
        else:
            source = ""

        (*params, trailing) = self.params

        assert " " not in self.command, "Space in {command!r}"
        for param in params:
            assert " " not in param, "Space in {param!r}"

        return f"{source}{self.command.upper()} {' '.join(params)} :{trailing}"
