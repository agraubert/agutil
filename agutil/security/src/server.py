from .connection import SecureConnection
from ...io import SocketServer

class SecureServer:
    def __init__(self, port, address='', queue=3, password=None, rsabits=4096, childverbose=False, childtimeout=3):
        self.port = port
        self.password = password
        self.rsabits = rsabits
        self.childverbose = childverbose
        self.childtimeout = childtimeout
        self.server = SocketServer(port, address, queue)

    def accept(self):
        socket = self.server.accept()
        return SecureConnection(socket, self.port, self.password, self.rsabits, self.childverbose, self.childtimeout)

    def close(self):
        self.server.close()
