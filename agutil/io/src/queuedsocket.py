from .socket import Socket
from socket import timeout as sockTimeout
from ... import Logger, DummyLog
import threading
import sys
import warnings

_QUEUEDSOCKET_IDENTIFIER_ = '<agutil.io.queuedsocket:1.0.0>'


class QueuedSocket(Socket):
    def __init__(
        self,
        address,
        port,
        logmethod=DummyLog,
        _socket=None
    ):
        warnings.warn(
            "QueuedSocket is now deprecated and will be"
            " removed in a future release",
            DeprecationWarning
        )
        super().__init__(address, port, _socket)
        self.incoming = {'__orphan__': []}
        self.outgoing = {}
        self.outgoing_index = 0
        self._shutdown = False
        self.datalock = threading.Condition()
        self.new_messages = threading.Event()
        self.message_sent = threading.Event()
        self._qs_log = logmethod
        if isinstance(self._qs_log, Logger):
            self._qs_log = self._qs_log.bindToSender("QueuedSocket")
        self._qs_log(
            "The underlying Socket has been initialized.  "
            "Starting background thread..."
        )
        self._thread = threading.Thread(
            target=QueuedSocket._worker,
            args=(self,),
            name="QueuedSocket background thread",
            daemon=True
        )
        self._thread.start()
        QueuedSocket.send(self, _QUEUEDSOCKET_IDENTIFIER_, '__protocol__')
        remoteID = QueuedSocket.recv(self, '__protocol__', True)
        if remoteID != _QUEUEDSOCKET_IDENTIFIER_:
            self._qs_log(
                "The remote socket provided an invalid QueuedSocket "
                "protocol identifier. (Theirs: %s) (Ours: %s)" % (
                    remoteID,
                    _QUEUEDSOCKET_IDENTIFIER_
                ),
                "WARN"
            )
            self.close()
            raise ValueError(
                "The remote socket provided an invalid identifier "
                "at the QueuedSocket level"
            )

    def close(self, timeout=1):
        if self._shutdown:
            return
        self._qs_log(
            "Shutdown initiated.  Waiting for background thread to "
            "send remaining messages (%d channels queued)" % len(self.outgoing)
        )
        with self.datalock:
            self._shutdown = True
        self._thread.join(timeout)
        super().close()
        self._qs_log.close()

    def send(self, msg, channel='__orphan__'):
        if self._shutdown:
            self._qs_log(
                "Attempt to use the QueuedSocket after shutdown",
                "WARN"
            )
            raise IOError("This QueuedSocket has already been closed")
        if '^' in channel:
            self._qs_log(
                "Attempt to send message over illegal channel name",
                "WARN"
            )
            raise ValueError(
                "Channel names cannot contain '^' characters (ascii 94)"
            )
        if type(msg) == str:
            msg = msg.encode()
        elif type(msg) != bytes:
            raise TypeError("msg argument must be str or bytes")
        if not self._thread.is_alive():
            self._qs_log(
                "The background thread has crashed or stopped before the "
                "QueuedSocket shut down.  Restarting thread...",
                "WARN"
            )
            self._thread = threading.Thread(
                target=QueuedSocket._worker,
                args=(self,),
                name="QueuedSocket background thread",
                daemon=True
            )
            self._thread.start()
            self._qs_log("The background thread has been restarted", "INFO")
        with self.datalock:
            if channel not in self.outgoing:
                self.outgoing[channel] = []
            self.outgoing[channel].append(msg)
        self._qs_log("Message Queued on channel '%s'" % channel, "DEBUG")

    def recv(
        self,
        channel='__orphan__',
        decode=False,
        timeout=None,
        _logInit=True
    ):
        if self._shutdown:
            self._qs_log(
                "Attempt to use the QueuedSocket after shutdown",
                "WARN"
            )
            raise IOError("This QueuedSocket has already been closed")
        if not self._thread.is_alive():
            self._qs_log(
                "The background thread has crashed or stopped before the "
                "QueuedSocket shut down.  Restarting thread...",
                "WARN"
            )
            self._thread = threading.Thread(
                target=QueuedSocket._worker,
                args=(self,),
                name="QueuedSocket background thread",
                daemon=True
            )
            self._thread.start()
            self._qs_log("The background thread has been restarted", "INFO")
        with self.datalock:
            if channel not in self.incoming:
                self.incoming[channel] = []
        if _logInit:
            self._qs_log(
                "Waiting for input on channel '%s'" % channel,
                "DEBUG"
            )
        while not self._check_channel(channel):
            result = self.new_messages.wait(timeout)
            if not result:
                raise sockTimeout()
            self.new_messages.clear()
        self._qs_log("Input dequeued from channel '%s'" % channel, "DETAIL")
        msg = self.incoming[channel].pop(0)
        if decode:
            msg = msg.decode()
        return msg

    def flush(self):
        while len(self.outgoing):
            self.message_sent.wait()
            self.message_sent.clear()

    def _sends(self, msg, channel):
        channel = ":ch#"+channel+"^"
        if type(msg) == bytes:
            channel = channel.encode()
        msg = channel + msg
        # print("Sends:", msg)
        super().send(msg)

    def _recvs(self):
        msg = super().recv()
        # print("Recvs:", msg)
        if msg[:4] == b':ch#':
            channel = b""
            i = 4
            while msg[i:i+1] != b'^':
                channel += msg[i:i+1]
                i += 1
            return (channel.decode(), msg[i+1:])
        return ("__orphan__", msg)

    def _check_channel(self, channel):
        return len(self.incoming[channel])

    def _worker(self):
        self._qs_log("QueuedSocket background thread initialized")
        outqueue = len(self.outgoing)
        while outqueue or not self._shutdown:
            if outqueue:
                with self.datalock:
                    self.outgoing_index = (self.outgoing_index + 1) % outqueue
                    target = list(self.outgoing)[self.outgoing_index]
                    payload = self.outgoing[target].pop(0)
                    self.outgoing = {
                        k: v for k, v in self.outgoing.items() if len(v)
                    }
                self._qs_log(
                    "Outgoing payload on channel '%s'" % target,
                    "DEBUG"
                )
                try:
                    self._sends(payload, target)
                    self.message_sent.set()
                except (OSError, BrokenPipeError) as e:
                    if self._shutdown:
                        self._qs_log(
                            "QueuedSocket background thread halted "
                            "(attempted to send after shutdown)"
                        )
                        return
                    else:
                        self._qs_log(
                            "QueuedSocket encountered an error: "+str(e),
                            "ERROR"
                        )
                        raise e
            if not self._shutdown:
                super().settimeout(.025)
                try:
                    (channel, payload) = self._recvs()
                    self._qs_log(
                        "Incoming payload on channel '%s'" % channel,
                        "DEBUG"
                    )
                    with self.datalock:
                        if channel not in self.incoming:
                            self.incoming[channel] = []
                    self.incoming[channel].append(payload)
                    self.new_messages.set()
                    self._qs_log(
                        "Threads waiting on '%s' have been notified" % channel,
                        "DETAIL"
                    )
                except sockTimeout:
                    pass
                except (OSError, BrokenPipeError) as e:
                    if self._shutdown:
                        self._qs_log("QueuedSocket background thread halted")
                        return
                    else:
                        self._qs_log(
                            "QueuedSocket encountered an error: "+str(e),
                            "ERROR"
                        )
                        raise e
            outqueue = len(self.outgoing)
