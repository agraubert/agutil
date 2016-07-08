from .socket import Socket
import threading
from socket import timeout, error

class QueuedSocket:
    def __init__(self, _socket):
        if type(_socket)!=Socket:
            raise TypeError("_socket argument must be of type agutil.io.Socket")
        self.sock = _socket
        self.inqueue = []
        self.outqueue = []
        self.shutdown = False
        self.iolock = threading.Condition()
        self._thread = threading.Thread(target=ioThread, args=(self,))
        self._thread.start()

    def recv(self, decode=False):
        if self.shutdown:
            self.close()
            raise IOError("This QueuedSocket has already been shutdown")
        self.iolock.acquire()
        self.iolock.wait_for(lambda :len(self.inqueue))
        output = self.inqueue.pop(0)
        self.iolock.release()
        if decode:
            return output.decode()
        return output

    def send(self, msg):
        if self.shutdown:
            self.close()
            raise IOError("This QueuedSocket has already been shutdown")
        self.iolock.acquire()
        self.outqueue.append(msg)
        self.iolock.release()

    def close(self):
        self.iolock.acquire()
        self.shutdown = True
        self.iolock.release()
        self._thread.join(2)
        self.sock.close()


def ioThread(owner):
    while not owner.shutdown:
        try:
            if len(owner.outqueue):
                owner.iolock.acquire()
                item = owner.outqueue.pop(0)
                owner.iolock.release()
                owner.sock.settimeout(None)
                owner.sock.send(item)
            else:
                owner.sock.settimeout(.2)
                item = None
                try:
                    item = owner.sock.recv()
                except timeout:
                    pass
                if item!=None:
                    owner.iolock.acquire()
                    owner.inqueue.append(item)
                    owner.iolock.notify_all()
                    owner.iolock.release()
        except error:
            break
