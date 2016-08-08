import socket
from .. import _PROTOCOL_IDENTIFIER_
from threading import RLock

_SOCKET_IDENTIFIER_ = '<agutil.io.socket:1.0.0>'
class Socket:
    def __init__(self, address, port, _socket=None, _skipIdentifier=False, _useIdentifier=_PROTOCOL_IDENTIFIER_+_SOCKET_IDENTIFIER_):
        self.addr = address
        self.port = port
        self.inlock = RLock()
        self.outlock = RLock()
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
        payload_size = len(msg)
        msg = format(payload_size, 'x').encode()+b'|' + msg
        msg_size = len(msg)
        # print("Sending: <", payload_size, ">",msg)
        # self.sock.send(b"|")
        test = self.inlock.acquire(False)
        if not test:
            print("Input locked")
        else:
            self.inlock.release()
        with self.inlock:
            while msg_size > 0:
                msg_size -= self.sock.send(msg)
                msg = msg[len(msg)-msg_size:]

    def recv(self, decode=False):
        msg = ""
        found_size = False
        size = ""
        test = self.outlock.acquire(False)
        if not test:
            print("Output locked")
        else:
            self.outlock.release()
        with self.outlock:
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
        return Socket(addr, self.port, sock)

    def close(self):
        self.sock.close()
