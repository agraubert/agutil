from .socket import Socket
from .queuedsocket import _QUEUEDSOCKET_IDENTIFIER_ as _MPLEXSOCKET_IDENTIFIER_
from socket import timeout as sockTimeout
from ... import Logger, DummyLog, context_lock, ActiveTimeout
from threading import RLock
from contextlib import contextmanager
import time

# _MPLEXSOCKET_IDENTIFIER_ = '<agutil.io.mplexsocket:1.0.0>'


class MPlexSocket(Socket):
    def __init__(
        self,
        address,
        port,
        logmethod=DummyLog,
        _socket=None
    ):
        super().__init__(address, port, _socket)
        self.iLock = RLock()
        self.oLock = RLock()
        self.closed = False
        # self.oLock = self.iLock
        self.queue = {}
        self._mp_log = logmethod
        MPlexSocket.send(self, _MPLEXSOCKET_IDENTIFIER_, '__protocol__')
        remoteID = MPlexSocket.recv(self, '__protocol__', True)
        if remoteID != _MPLEXSOCKET_IDENTIFIER_:
            self._mp_log(
                "The remote socket provided an invalid MPlexSocket "
                "protocol identifier. (Theirs: %s) (Ours: %s)" % (
                    remoteID,
                    _MPLEXSOCKET_IDENTIFIER_
                ),
                "WARN"
            )
            self.close()
            raise ValueError(
                "The remote socket provided an invalid identifier "
                "at the MPlexSocket level"
            )

    def close(self):
        self.closed = True
        super().close()

    def flush(self):
        pass

    @contextmanager
    def use_timeout(self, t):
        if self.closed:
            raise OSError("This socket has been closed")
        old = super().gettimeout()
        try:
            super().settimeout(t)
            yield
        finally:
            super().settimeout(old)

    def send(self, message, channel='__orphan__'):
        if self.closed:
            raise OSError("This socket has been closed")
        if '^' in channel:
            self._mp_log(
                "Attempt to send message over illegal channel name",
                "WARN"
            )
            raise ValueError(
                "Channel names cannot contain '^' characters (ascii 94)"
            )
        if type(message) == str:
            message = message.encode()
        elif type(message) != bytes:
            raise TypeError("msg argument must be str or bytes")
        with self.oLock:
            msg = b':ch#' + channel.encode() + b'^' + message
            super().send(msg)

    def recv(
        self,
        channel='__orphan__',
        decode=False,
        timeout=None,
        _loginit=True
    ):
        if self.closed:
            raise OSError("This socket has been closed")
        if _loginit:
            self._mp_log(
                "Receive message on channel %s with timeout %s" % (
                    channel,
                    timeout
                ),
                'DETAIL'
            )
        with ActiveTimeout(timeout) as timer:
            sleep_time = 0
            while True:
                if channel in self.queue and len(self.queue[channel]):
                    self._mp_log(
                        "Reading previously queued message",
                        'DEBUG'
                    )
                    # with context_lock(self.iLock, timer.thread_timeout):
                    with self.iLock:
                        result = self.queue[channel].pop(0)
                        if decode:
                            result = result.decode()
                        return result
                with context_lock(self.iLock, timer.thread_timeout):
                    if _loginit:
                        self._mp_log(
                            "Attempting to receive new message",
                            "DEBUG"
                        )
                    with self.use_timeout(timer.socket_timeout):
                        msg = super().recv()
                        if msg[:4] == b':ch#':
                            ch = b""
                            i = 4
                            while i < len(msg) and msg[i:i+1] != b'^':
                                ch += msg[i:i+1]
                                i += 1
                            if i > len(msg):
                                ch, message = "__orphan__", msg
                            else:
                                ch, message = ch.decode(), msg[i+1:]
                        else:
                            ch, message = "__orphan__", msg
                        self._mp_log(
                            "New message received on channel %s" % channel,
                            "DETAIL"
                        )
                        try:
                            sleep_time = timer.socket_timeout
                        except sockTimeout:
                            sleep_time = timeout
                        timer.reset()
                    if ch == channel:
                        if decode:
                            message = message.decode()
                        return message
                    elif ch not in self.queue:
                        self.queue[ch] = [message]
                    else:
                        self.queue[ch].append(message)
                if sleep_time is None:
                    time.sleep(1)
                elif sleep_time > 0:
                    time.sleep(0.05)
                    sleep_time = 0
                    timer.reset()
