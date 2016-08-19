import socket
from .. import _PROTOCOL_IDENTIFIER_

_SOCKET_IDENTIFIER_ = '<agutil.io.socket:1.0.0>'
class Socket:
    def __init__(self, address, port, _socket=None, _skipIdentifier=False, _useIdentifier=_PROTOCOL_IDENTIFIER_+_SOCKET_IDENTIFIER_):
        self.addr = address
        self.port = port
        if _socket!=None:
            self.sock = _socket
        else:
            self.sock = socket.socket()
            self.sock.connect((address, port))
        self.rollover = b""
        if not _skipIdentifier:
            self.send(_useIdentifier)
            remoteID = self.recv(True)
            if remoteID != _useIdentifier:
                self.close()
                raise ValueError("The remote socket provided an invalid identifier at the Socket level")

    def send(self, msg):
        if type(msg)==str:
            msg=msg.encode()
        elif type(msg)!=bytes:
            raise TypeError("msg argument must be str or bytes")
        msg += b'\x00\x02'
        payload_size = len(msg)
        # print("Sending: <", payload_size, ">",msg)
        msg = format(payload_size, 'x').encode()+b'|'+msg
        msg_size = len(msg)
        while msg_size > 0:
            msg_size -= self.sock.send(msg)
            msg = msg[len(msg)-msg_size:]

    def recv(self, decode=False):
        msg = ""
        found_size = False
        size = ""
        while not found_size:
            if len(self.rollover):
                intake = self.rollover
            else:
                intake = self.sock.recv(4096)
            for i in range(len(intake)):
                current = intake[i:i+1]
                if current == b'|':
                    size = int(size, 16)
                    msg = intake[i+1:i+1+size]
                    self.rollover = intake[i+1+size:]
                    found_size = True
                    break
                else:
                    size+=current.decode()

        while len(msg) < size:
            msg += self.sock.recv(min(4096, size-len(msg)))

        if not msg.endswith(b'\x00\x02'):
            raise IOError("Received message with invalid padding bytes")
        if decode:
            return msg[:-2].decode()
        # print("Received: <", size, ">", msg)
        return msg[:-2]

    def settimeout(self, time):
        self.sock.settimeout(time)

    def gettimeout(self):
        return self.sock.gettimeout()

    def close(self):
        try:
            self.sock.setblocking(True)
            self.sock.shutdown(socket.SHUT_RDWR)
        except OSError:
            pass
        finally:
            self.sock.close()


class SocketServer:
    def __init__(self, port, address='', queue=3):
        self.port = port
        self.sock = socket.socket()
        self.sock.bind((address, port))
        self.sock.listen(queue)

    def accept(self):
        (sock, addr) = self.sock.accept()
        return Socket(addr, self.port, sock)

    def close(self):
        self.sock.close()
