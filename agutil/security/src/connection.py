from .securesocket import SecureSocket
from ... import io, Logger, DummyLog, byteSize, ActiveTimeout
from . import protocols
from socket import timeout as socketTimeout
import threading
import random
import os
import time
import rsa

random.seed()

_SECURECONNECTION_IDENTIFIER_ = '<agutil.security.secureconnection:2.0.0>'


class SecureConnection:
    def __init__(
        self,
        address,
        port,
        password=None,
        rsabits=4096,
        timeout=3,
        logmethod=DummyLog,
        _socket=None
    ):
        if isinstance(logmethod, Logger):
            self.log = logmethod.bindToSender("SecureConnection")
        else:
            self.log = logmethod
        if address == '' or address == 'listen':
            ss = io.SocketServer(port, queue=0)
            self.sock = ss.accept(
                SecureSocket,
                password=password,
                rsabits=rsabits,
                timeout=None,
                logmethod=self.log.bindToSender(self.log.name+"->SecureSocket")
            )
            ss.close()
        elif _socket is not None:
            self.sock = _socket
            self.sock.log = self.log.bindToSender(
                self.log.name+'->SecureSocket'
            )
        else:
            self.sock = SecureSocket(
                address,
                port,
                password,
                rsabits,
                None,
                self.log.bindToSender(self.log.name+"->SecureSocket")
            )
        self.log(
            "SecureConnection now initialized.  Starting background threads..."
        )
        self.pending_transfers = {}
        self.pending_confirmations = {}

        self.sock.sendRAW(_SECURECONNECTION_IDENTIFIER_, '__protocol__')
        remoteID = self.sock.recvRAW('__protocol__', True)
        if remoteID != _SECURECONNECTION_IDENTIFIER_:
            self.log(
                "The remote socket provided an invalid SecureConnection "
                "protocol identifier. (Theirs: %s) (Ours: %s)" % (
                    remoteID,
                    _SECURECONNECTION_IDENTIFIER_
                ),
                "WARN"
            )
            self.close()
            raise ValueError(
                "The remote socket provided an invalid identifier "
                "at the SecureConnection level"
            )

        self.sock.settimeout(timeout)

    def _reserve_task(self, prefix):
        return prefix+"_"+str(time.time())+"".join(
            str(random.randint(0, 9)) for _ in range(5)
        )

    def send(self, msg):
        if type(msg) == str:
            msg = msg.encode()
        elif type(msg) != bytes:
            self.log(
                "Attempt to send message which was not str or bytes",
                "WARN"
            )
            raise TypeError("msg argument must be str or bytes")
        self.log("Outgoing text message scheduled", "INFO")
        channel = self._reserve_task('TEXT')
        self.sock.sendAES(
            channel,
            '__text__'
        )
        self.log("Sending message payload", "DEBUG")
        self.sock.sendRSA(
            msg,
            channel
        )
        return channel

    def _send_confirm(self, task, success=True):
        self.sock.sendAES(
            task + ('+' if success else '-'),
            '__conf__'
        )

    def confirm(self, task, timeout=-1):
        if timeout == -1:
            timeout = self.sock.timeout
        self.log("Waiting for task confirmation", 'DEBUG')
        with ActiveTimeout(timeout) as timer:
            while task not in self.pending_confirmations:
                conf = self.sock.recvAES(
                    '__conf__',
                    True,
                    timer.socket_timeout
                )
                with self.sock.syncLock:
                    self.pending_confirmations[conf[:-1]] = conf[-1] == '+'
        with self.sock.syncLock:
            result = self.pending_confirmations[task]
            del self.pending_confirmations[task]
        return result

    def read(self, decode=True, timeout=-1):
        if timeout == -1:
            timeout = self.sock.timeout
        self.log("Waiting for text syncup", 'DEBUG')
        with ActiveTimeout(timeout) as timer:
            channel = self.sock.recvAES(
                '__text__',
                True,
                timeout=timer.socket_timeout
            )
            try:
                message = self.sock.recvRSA(
                    channel,
                    timeout=timer.socket_timeout
                )
            except rsa.pkcs1.VerificationError:
                self._send_confirm(channel, False)
                self.log(
                    "RSA Message failed signature validation",
                    "WARN"
                )
                raise
            except BaseException:
                self._send_confirm(channel, False)
                self.log(
                    "Encountered an error reading RSA message",
                    'ERROR'
                )
                raise
        self._send_confirm(channel)
        if decode:
            message = message.decode()
        return message

    def sendfile(self, filename):
        self.log("Preparing file transfer", "INFO")
        channel = self._reserve_task('FILE')
        with self.sock.syncLock:
            self.pending_transfers[channel] = threading.Thread(
                target=SecureConnection._transfer,
                args=(self, channel, filename),
                daemon=True
            )
        self.pending_transfers[channel].start()
        self.sock.sendAES(
            protocols.packcmd(
                'FILE',
                {
                    'channel': channel,
                    'filename': os.path.basename(filename),
                    'size': str(os.path.getsize(filename))
                }
            ),
            '__file__',
            True
        )
        return channel

    def _transfer(self, channel, filename):
        try:
            response = self.sock.recvRAW(channel, decode=True, timeout=None)
            if response == '+':
                with open(filename, 'rb') as reader:
                    self.sock.sendAES(
                        reader,
                        channel,
                        True,
                        True
                    )
            with self.sock.syncLock:
                del self.pending_transfers[channel]
        except BaseException as e:
            self.log(
                "Background transfer failed: " + repr(e),
                'ERROR'
            )
            with self.sock.syncLock:
                self.pending_confirmations[channel] = False

    def savefile(self, destination=None, timeout=-1, force=False):
        if timeout == -1:
            timeout = self.sock.timeout
        self.log("Waiting to receive incoming file request", "INFO")
        with ActiveTimeout(timeout) as timer:
            metadata = protocols.unpackcmd(
                self.sock.recvAES(
                    '__file__',
                    timeout=timer.socket_timeout
                )
            )
            self.log(
                "Acquired file transfer request. Reading metadata",
                "DEBUG"
            )
        try:
            if destination is None:
                destination = metadata['filename']
            if not force:
                print(
                    "The remote socket is attempting to send the "
                    "file '%s'" % metadata['filename']
                )
                print("Size:", byteSize(int(metadata['size'])))
                accepted = False
                choice = ""
                while not accepted:
                    choice = input("Accept this transfer (y/n): ")
                    choice = choice.lower()
                    if choice not in {'y', 'n', 'yes', 'no'}:
                        print("Please enter y, Y, yes, n, N, or no")
                    else:
                        accepted = True
                if choice[0] != 'y':
                    self.log(
                        "User rejected transfer of file '%s'" % (
                            metadata['filename']
                        )
                    )
                    self.sock.sendRAW('-', metadata['channel'])
                    self._send_confirm(metadata['channel'], False)
                    return
            self.log("Accepted transfer of file '%s'" % metadata['filename'])
            self.sock.sendRAW('+', metadata['channel'])
            self.log("Starting transfer...", "INFO")
            self.sock.recvAES(
                metadata['channel'],
                output_file=destination,
                timeout=timeout
            )
            self._send_confirm(metadata['channel'])
        except BaseException:
            if 'channel' in metadata:
                self._send_confirm(metadata['channel'], False)
            raise
        return destination

    def shutdown(self):
        self.close(timeout)

    def close(self):
        self.sock.close()
        self.log.close()

    def flush(self):
        while len(self.pending_transfers):
            self.pending_transfers[0].join()
