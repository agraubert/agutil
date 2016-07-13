import socket

class Socket:
    def __init__(self, address, port, _socket=None):
        self.addr = address
        self.port = port
        if _socket!=None:
            self.sock = _socket
        else:
            self.sock = socket.socket()
            self.sock.connect((address, port))
        self.rollover = b""

    def send(self, msg):
        if type(msg)==str:
            msg=msg.encode()
        elif type(msg)!=bytes:
            raise TypeError("msg argument must be str or bytes")
        payload_size = len(msg)
        # print("Sending: <", payload_size, ">",msg)
        self.sock.send(format(payload_size, 'x').encode())
        self.sock.send(b"|")
        while payload_size > 0:
            payload_size -= self.sock.send(msg)
            msg = msg[len(msg)-payload_size:]

    def recv(self, decode=False):
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
