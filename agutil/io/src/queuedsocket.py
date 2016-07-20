from .socket import Socket
from socket import timeout as sockTimeout
import threading

class QueuedSocket(Socket):
    def __init__(self, socket, _debug=False):
        if not isinstance(socket, Socket):
            raise TypeError("socket argument must be of type agutil.io.Socket")
        super().__init__(socket.addr, socket.port, socket.sock)
        self.incoming = {'__orphan__': []}
        self.outgoing = {}
        self.outgoing_channels = []
        self._shutdown = False
        self.datalock = threading.Condition()
        self.iolock = threading.Condition()
        self._debug = _debug
        self._thread = threading.Thread(
            target=QueuedSocket._worker,
            args=(self,),
            name="QueuedSocket background thread",
            daemon=True
        )
        self._thread.start()

    def close(self, timeout=1):
        self.datalock.acquire()
        self._shutdown = True
        self.datalock.release()
        self._thread.join(timeout)
        super().close()

    def send(self, msg, channel='__orphan__'):
        if self._shutdown:
            raise IOError("This QueuedSocket has already been closed")
        if '|' in channel:
            raise ValueError("Channel names cannot contain '|' characters (ascii 124)")
        self.datalock.acquire()
        if channel not in self.outgoing:
            self.outgoing[channel] = [msg]
        else:
            self.outgoing[channel].append(msg)
        if self._debug:
            print("Queued output on channel", channel)
        self.outgoing_channels.append(""+channel)
        self.datalock.release()

    def recv(self, channel='__orphan__', decode=False, timeout=None):
        if self._shutdown:
            raise IOError("This QueuedSocket has already been closed")
        self.datalock.acquire()
        if channel not in self.incoming:
            self.incoming[channel] = []
        if not self._check_channel(channel):
            if self._debug:
                print("Waiting for input on channel", channel)
            result = self.datalock.wait_for(lambda :self._check_channel(channel), timeout)
            if not result:
                self.datalock.release()
                raise sockTimeout()
            if self._debug:
                print("Input dequeued")
        msg = self.incoming[channel].pop(0)
        self.datalock.release()
        if decode:
            msg = msg.decode()
        return msg

    def _sends(self, msg, channel):
        channel = ":ch#"+channel+"|"
        if type(msg)==bytes:
            channel = channel.encode()
        msg = channel + msg
        # print("Sends:", msg)
        self.iolock.acquire()
        super().send(msg)
        self.iolock.release()

    def _recvs(self):
        self.iolock.acquire()
        msg = super().recv()
        self.iolock.release()
        # print("Recvs:", msg)
        if msg[:4] == b':ch#':
            channel = b""
            i = 4
            while msg[i:i+1] != b'|':
                channel += msg[i:i+1]
                i+=1
            return (channel.decode(), msg[i+1:])
        return ("__orphan__", msg)

    def _check_channel(self, channel):
        return len(self.incoming[channel])

    def _worker(self):
        if self._debug:
            print("Worker started")
        while True:
            self.datalock.acquire()
            status = self._shutdown
            outqueue = len(self.outgoing_channels)
            self.datalock.release()
            if status:
                if self._debug:
                    print("QueuedSocket worker stopped")
                return
            if outqueue:
                self.datalock.acquire()
                target = self.outgoing_channels.pop(0)
                payload = self.outgoing[target].pop(0)
                self.datalock.release()
                if self._debug:
                    print("Outgoing payload on channel", target)
                try:
                    self._sends(payload, target)
                except OSError as e:
                    if self._shutdown:
                        if self._debug:
                            print("QueuedSocket worker stopped")
                        return
                    else:
                        raise e
            super().settimeout(.05)
            try:
                (channel, payload) = self._recvs()
                if self._debug:
                    print("Incoming payload on channel", channel)
                self.datalock.acquire()
                if channel not in self.incoming:
                    self.incoming[channel] = []
                self.incoming[channel].append(payload)
                self.datalock.notify_all()
                if self._debug:
                    print("Threads waiting on", channel, "have been notified")
                self.datalock.release()
            except sockTimeout:
                pass
            except OSError as e:
                if self._shutdown:
                    if self._debug:
                        print("QueuedSocket worker stopped")
                    return
                else:
                    raise e
