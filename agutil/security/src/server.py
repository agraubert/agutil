from .connection import SecureConnection
from .securesocket import SecureSocket
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
        socket = self.server.accept(
            SecureSocket,
            password=self.password,
            rsabits=self.rsabits,
            timeout=self.childtimeout,
            logmethod=self.childlogger
        )
        return SecureConnection(
            socket.addr,
            self.port,
            self.password,
            self.rsabits,
            self.childtimeout,
            self.childlogger,
            _socket=socket
        )

    def close(self):
        self.server.close()
