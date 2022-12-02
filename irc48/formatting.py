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

import re

_NONCOLORS = [
    ("\x02", "\x1b[1m"),  # bold
    ("\x1d", "\x1b[3m"),  # italic
    ("\x1f", "\x1b[4m"),  # underline
    ("\x1e", "\x1b[9m"),  # strikethrough
    ("\x0f", "\x1b[0m"),  # reset
]

_COLORS = [
    ("0", "7"),  # White.
    ("1", "0"),  # Black.
    ("2", "4"),  # Blue.
    ("3", "2"),  # Green.
    ("4", "1"),  # Red.
    ("5", "8;5;94"),  # Brown.
    ("6", "3"),  # Magenta.
    ("7", "8;5;215"),  # Orange.
    ("8", "3"),  # Yellow.
    ("9", "2"),  # Light Green.
    ("10", "6"),  # Cyan.
    ("11", "8;5;159"),  # Light Cyan.
    ("12", "8;5;39"),  # Light Blue.
    ("13", "8;5;219"),  # Pink.
    ("14", "8;5;7"),  # Grey.
    ("15", "8;5;15"),  # Light Grey.
]

# Copied from https://modern.ircdocs.horse/formatting.html#colors-16-98
_100_COLORS = """
16 52 	17 94 	18 100 	19 58 	20 22 	21 29 	22 23 	23 24 	24 17 	25 54 	26 53 	27 89
28 88 	29 130 	30 142 	31 64 	32 28 	33 35 	34 30 	35 25 	36 18 	37 91 	38 90 	39 125
40 124 	41 166 	42 184 	43 106 	44 34 	45 49 	46 37 	47 33 	48 19 	49 129 	50 127 	51 161
52 196 	53 208 	54 226 	55 154 	56 46 	57 86 	58 51 	59 75 	60 21 	61 171 	62 201 	63 198
64 203 	65 215 	66 227 	67 191 	68 83 	69 122 	70 87 	71 111 	72 63 	73 177 	74 207 	75 205
76 217 	77 223 	78 229 	79 193 	80 157 	81 158 	82 159 	83 153 	84 147 	85 183 	86 219 	87 212
88 16 	89 233 	90 235 	91 237 	92 239 	93 241 	94 244 	95 247 	96 250 	97 254 	98 231
""".split()

_IRC_COLOR_TO_ANSI = {
    **dict(_COLORS),
    **dict(zip(_100_COLORS[::2], map("8;5;".__add__, _100_COLORS[1::2]))),
}

_IRC_COLOR_RE = re.compile(
    "\x03(?P<foreground>[0-9]{0,2})(,(?P<background>[0-9]{0,2}))?"
)

_IRC_256COLOR_RE = re.compile(r"\x04(?P<r>\d\d)(?P<g>\d\d)(?P<b>\d\d)")


def _irc_color_replacer(m: re.Match[str]) -> str:
    s = ""
    if foreground := m.group("foreground"):
        try:
            s += "\x1b[3" + _IRC_COLOR_TO_ANSI[foreground] + "m"
        except KeyError:
            pass
    if background := m.group("background"):
        try:
            s += "\x1b[4" + _IRC_COLOR_TO_ANSI[background] + "m"
        except KeyError:
            pass

    return s


def irc_to_ansi(s: str) -> str:
    s += "\x0f"
    for (irc_code, ansi_code) in _NONCOLORS:
        s = s.replace(irc_code, ansi_code)
    s = _IRC_COLOR_RE.sub(_irc_color_replacer, s)
    return s
