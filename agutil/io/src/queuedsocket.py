from .socket import Socket
from .protocol_identifier import _PROTOCOL_IDENTIFIER_, parseIdentifier, checkIdentifier
from socket import timeout as sockTimeout
from ... import Logger, DummyLog
import threading

_QUEUEDSOCKET_VERSION_ = '1.0.0'
_QUEUEDSOCKET_IDENTIFIER_ = '<agutil.io.queuedsocket:%s>'%_QUEUEDSOCKET_VERSION_

class QueuedSocket(Socket):
    def __init__(self, socket,  upstreamIdentifier=_PROTOCOL_IDENTIFIER_, logmethod=DummyLog):
        if not isinstance(socket, Socket):
            raise TypeError("socket argument must be of type agutil.io.Socket")
        _upstreamID = upstreamIdentifier+_QUEUEDSOCKET_IDENTIFIER_
        super().__init__(socket.addr, socket.port, _upstreamID, socket.sock)
        if not checkIdentifier(self.remoteIdentifier, 'agutil.io.queuedsocket', _QUEUEDSOCKET_VERSION_):
            raise ValueError("Invalid remote protocol identifier at QueuedSocket level")
        self.incoming = {'__orphan__': []}
        self.outgoing = {}
        self.outgoing_channels = []
        self._shutdown = False
        self.datalock = threading.Condition()
        self.iolock = threading.Condition()
        self.log = logmethod
        if isinstance(self.log, Logger):
            self.log = self.log.bindToSender("QueuedSocket")
        self.log("The underlying Socket has been initialized.  Starting background thread...")
        self._thread = threading.Thread(
            target=QueuedSocket._worker,
            args=(self,),
            name="QueuedSocket background thread",
            daemon=True
        )
        self._thread.start()

    def close(self, timeout=1):
        if self._shutdown:
            return
        self.log("Shutdown initiated")
        self.datalock.acquire()
        self._shutdown = True
        self.datalock.release()
        self._thread.join(timeout)
        super().close()
        self.log.close()

    def send(self, msg, channel='__orphan__'):
        if self._shutdown:
            self.log("Attempt to use the QueuedSocket after shutdown", "WARN")
            raise IOError("This QueuedSocket has already been closed")
        if '|' in channel:
            self.log("Attempt to send message over illegal channel name", "WARN")
            raise ValueError("Channel names cannot contain '|' characters (ascii 124)")
        self.datalock.acquire()
        if channel not in self.outgoing:
            self.outgoing[channel] = [msg]
        else:
            self.outgoing[channel].append(msg)
        self.log("Message Queued on channel '%s'"%channel, "DEBUG")
        self.outgoing_channels.append(""+channel)
        self.datalock.release()

    def recv(self, channel='__orphan__', decode=False, timeout=None):
        if self._shutdown:
            self.log("Attempt to use the QueuedSocket after shutdown", "WARN")
            raise IOError("This QueuedSocket has already been closed")
        self.datalock.acquire()
        if channel not in self.incoming:
            self.incoming[channel] = []
        if not self._check_channel(channel):
            self.log("Waiting for input on channel '%s'" %channel, "DEBUG")
            result = self.datalock.wait_for(lambda :self._check_channel(channel), timeout)
            if not result:
                self.datalock.release()
                raise sockTimeout()
            self.log("Input dequeued from channel '%s'"%channel, "DETAIL")
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
        self.log("QueuedSocket background thread initialized")
        while True:
            self.datalock.acquire()
            status = self._shutdown
            outqueue = len(self.outgoing_channels)
            self.datalock.release()
            if status:
                self.log("QueuedSocket background thread halted")
                return
            if outqueue:
                self.datalock.acquire()
                target = self.outgoing_channels.pop(0)
                payload = self.outgoing[target].pop(0)
                self.datalock.release()
                self.log("Outgoing payload on channel '%s'" %target, "DEBUG")
                try:
                    self._sends(payload, target)
                except OSError as e:
                    if self._shutdown:
                        self.log("QueuedSocket background thread halted")
                        return
                    else:
                        self.log("QueuedSocket encountered an error: "+str(e), "ERROR")
                        raise e
            super().settimeout(.05)
            try:
                (channel, payload) = self._recvs()
                self.log("Incoming payload on channel '%s'" %channel, "DEBUG")
                self.datalock.acquire()
                if channel not in self.incoming:
                    self.incoming[channel] = []
                self.incoming[channel].append(payload)
                self.datalock.notify_all()
                self.log("Threads waiting on '%s' have been notified" %channel, "DETAIL")
                self.datalock.release()
            except sockTimeout:
                pass
            except OSError as e:
                if self._shutdown:
                    self.log("QueuedSocket background thread halted")
                    return
                else:
                    self.log("QueuedSocket encountered an error: "+str(e), "ERROR")
                    raise e
