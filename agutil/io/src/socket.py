import socket
from .protocol_identifier import _PROTOCOL_IDENTIFIER_, parseIdentifier, checkIdentifier

_SOCKET_VERSION_ = '1.0.0'
_SOCKET_IDENTIFIER_ = '<agutil.io.socket:%s>'%_SOCKET_VERSION_

class Socket:
    def __init__(self, address, port, upstreamIdentifier=_PROTOCOL_IDENTIFIER_, _socket=None):
        self.addr = address
        self.port = port
        self.rawIdentifier = upstreamIdentifier+_SOCKET_IDENTIFIER_
        self.identifier = parseIdentifier(self.rawIdentifier)[0]
        if _socket!=None:
            self.sock = _socket
        else:
            self.sock = socket.socket()
            self.sock.connect((address, port))
        self.rollover = b""
        self._base_send(self.rawIdentifier)
        (self.remoteIdentifier, base_check) = parseIdentifier(self._base_recv(True))
        if not (base_check and checkIdentifier(self.remoteIdentifier, 'agutil.io.socket', _SOCKET_VERSION_)):
            raise ValueError("Invalid remote protocol identifier at Socket level")

    def send(self, msg):
        self._base_send(msg)

    def _base_send(self, msg):
        if type(msg)==str:
            msg=msg.encode()
        elif type(msg)!=bytes:
            raise TypeError("msg argument must be str or bytes")
        payload_size = len(msg)
        # print("Sending: <", payload_size, ">",msg)
        self.sock.send(format(payload_size, 'x').encode()+b'|')
        # self.sock.send(b"|")
        while payload_size > 0:
            payload_size -= self.sock.send(msg)
            msg = msg[len(msg)-payload_size:]

    def recv(self, decode=False):
        return self._base_recv(decode)

    def _base_recv(self, decode=False):
        msg = ""
        found_size = False
        size = ""
        while not found_size:
            intake = self.rollover + self.sock.recv(4096)
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

        if decode:
            return msg.decode()
        # print("Received: <", size, ">", msg)
        return msg

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
        return Socket(addr, self.port, _socket=sock)

    def close(self):
        self.sock.close()
