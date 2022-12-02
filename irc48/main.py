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

import queue
import sys
import threading

from .connection import Connection
from .state import State
from .ui import UI


def main(argv: list[str]):
    try:
        (_, hostname, port_s, nick) = argv
        port = int(port_s)
    except ValueError:
        print("Syntax: python3 -m irc48 <hostname> <port> <nick>", file=sys.stderr)
        exit(1)

    state = State(default_nick=nick)
    connection = Connection(hostname, port, tls=True)
    ui = UI(state)

    try:
        state.attach_ui(ui)
        state.attach_connection(connection)

        connection_thread = threading.Thread(target=connection.loop, args=(state,))
        ui.start()
        input_thread = threading.Thread(target=ui.loop_input)
        display_thread = threading.Thread(target=ui.loop_display)

        connection_thread.start()
        input_thread.start()
        display_thread.start()

        connection_thread.join()
        input_thread.join()
        display_thread.join()
    except KeyboardInterrupt:
        state.shut_down = True
