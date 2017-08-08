from .connection import SecureConnection
from ...io import SocketServer
from ... import Logger, DummyLog


class SecureServer:
    def __init__(
        self,
        port,
        address='',
        queue=3,
        password=None,
        rsabits=4096,
        childtimeout=3,
        childlogger=DummyLog
    ):
        self.port = port
        self.password = password
        self.rsabits = rsabits
        self.childlogger = childlogger
        self.childtimeout = childtimeout
        self.server = SocketServer(port, address, queue)

    def accept(self):
        socket = self.server.accept()
        return SecureConnection(
            socket,
            self.port,
            self.password,
            self.rsabits,
            self.childtimeout,
            self.childlogger
        )

    def close(self):
        self.server.close()
