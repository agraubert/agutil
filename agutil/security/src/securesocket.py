from ... import io, Logger, DummyLog, intToBytes, bytesToInt
import hashlib
import rsa
import os
import Cryptodome.Cipher.AES as AES
from io import BytesIO, BufferedReader, BufferedWriter
from . import protocols, cipher as Cipher
from threading import Lock, Condition
import random

from socket import timeout as socketTimeout

_SECURESOCKET_IDENTIFIER_ = '<agutil.security.securesocket:4.0.0>'

RSA_CPU = None
try:
    RSA_CPU = os.cpu_count()
    if RSA_CPU is None:
        RSA_CPU = 2
    RSA_CPU = int(RSA_CPU/2)
    if not RSA_CPU:
        RSA_CPU = 1
except AttributeError:
    RSA_CPU = 1


class _dummyCipher:
    def encrypt(self, msg):
        return msg

    def decrypt(self, msg):
        return msg


class SecureSocket(io.MPlexSocket):
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
            self._ss_log = logmethod.bindToSender("SecureSocket")
        else:
            self._ss_log = logmethod
        super().__init__(
            address,
            port,
            logmethod=self._ss_log.bindToSender(
                self._ss_log.name+"->MPlexSocket"
            ),
            _socket=_socket
        )
        self._ss_log(
            "The underlying MPlexSocket has been initialized.  "
            "Exchanging encryption data now"
        )
        self.rsabits = rsabits
        if not (timeout is None or type(timeout) == int):
            raise TypeError("Timeout parameter must be an integer or None")
        if type(timeout) == int and timeout < 0:
            raise ValueError("Timeout cannot be negative")
        self.timeout = timeout
        protocolstring = _SECURESOCKET_IDENTIFIER_
        if password is not None:
            protocolstring += "<agutil.security.securesocket.password:%s>" % (
                hashlib.sha512(
                    hashlib.sha512(password.encode()+b"lol").digest()
                ).hexdigest()
            )
            self.baseCipher = AES.new(
                hashlib.sha256(password.encode()).digest(),
                AES.MODE_ECB
            )
        else:
            self.baseCipher = _dummyCipher()
        self._ss_log("Sending protocol identifier", "DETAIL")
        self._sendq(protocolstring, '__protocol__')
        self._ss_log("Receiving remote identifier", "DETAIL")
        remoteprotocol = self._recvq(
            '__protocol__',
            decode=True,
            timeout=timeout
        )
        if remoteprotocol != protocolstring:
            self._ss_log(
                "The remote socket provided an invalid SecureSocket "
                "protocol identifier. (Theirs: %s) (Ours: %s)" % (
                    remoteprotocol,
                    protocolstring
                ),
                "WARN"
            )
            self.close()
            raise ValueError(
                "The remote socket provided an invalid protocol "
                "identifier at the SecureSocket level"
            )
        self._ss_log("Sending encryption confirmation", "DETAIL")
        self._sendq(self._baseEncrypt('OK'), '__control__')
        self._ss_log("Receiving remote encryption confirmation", "DETAIL")
        if (self._baseDecrypt(
            self._recvq('__control__', timeout=timeout)
        ) != b'OK'):
            self._ss_log(
                "Unable to confirm base encryption with the remote socket."
                "  Are you sure you entered the correct password?",
                "WARN"
            )
            self.close()
            raise ValueError(
                "Unable to confirm base encryption with the remote socket."
                "Are you sure you entered the correct password?"
            )
        self._ss_log("Sending RSA keysize", "DETAIL")
        self._sendq(self._baseEncrypt(format(rsabits, 'x')), '__control__')
        self._ss_log("Receiving remote RSA keysize", "DETAIL")
        self.remote_rsabits = int(self._baseDecrypt(self._recvq(
            '__control__',
            timeout=timeout
        )).decode(), 16)
        self.maxsize = int((self.remote_rsabits / 8)) - 16
        self._ss_log("Generating RSA keypair", "DEBUG")
        (self.pub, self.priv) = rsa.newkeys(rsabits, True, RSA_CPU)
        self._ss_log("Sending RSA pubkey", "DETAIL")
        self._sendq(self._baseEncrypt(intToBytes(self.pub.n)), '__control__')
        self._sendq(self._baseEncrypt(intToBytes(self.pub.e)), '__control__')
        self._ss_log("Receiving remote RSA pubkey", "DETAIL")
        _n = bytesToInt(self._baseDecrypt(self._recvq('__control__')))
        _e = bytesToInt(self._baseDecrypt(self._recvq('__control__')))
        self.rpub = rsa.PublicKey(_n, _e)
        self._ss_log("Confirming encryption", "DEBUG")
        self._sendq(rsa.encrypt(
            b'OK',
            self.rpub
        ), '__control__')
        response = rsa.decrypt(
            self._recvq('__control__', timeout=timeout),
            self.priv
        )
        if response != b'OK':
            self._ss_log(
                "Unable to confirm RSA encryption with the remote socket.",
                "WARN"
            )
            self.close()
            raise ValueError(
                "Unable to confirm RSA encryption with the remote socket."
            )
        random.seed()
        syncSeed = random.random()
        self._sendq(str(syncSeed), '__control__')
        tmp = float(self._recvq('__control__', decode=True))
        self.sync_tail = '-' if syncSeed > tmp else '+'
        self.synced_channels = set()
        # self.syncLock = Lock()
        self.syncLock = Condition()

    def _sendq(self, msg, channel='__orphan__'):
        super().send(msg, channel)

    def _recvq(
        self,
        channel='__orphan__',
        decode=False,
        timeout=None,
        _logInit=True
    ):
        return super().recv(channel, decode, timeout, _logInit)

    def _baseEncrypt(self, msg):
        return self.baseCipher.encrypt(
            protocols.padstring(msg)
        )

    def _baseDecrypt(self, msg):
        return protocols.unpadstring(
            self.baseCipher.decrypt(msg)
        )

    def _sync_channel(self, channel):
        self.syncLock.acquire()
        name = channel+"::"+"".join(
            str(random.randint(0, 9)) for _ in range(10)
        ) + self.sync_tail
        while name in self.synced_channels:
            name = channel+"::"+"".join(
                str(random.randint(0, 9)) for _ in range(10)
            ) + self.sync_tail
        self.synced_channels.add(name)
        self._sendq(name, 'sync//%s' % channel)
        self.syncLock.release()
        return name

    def _desync_channel(self, channel):
        self.syncLock.acquire()
        self.synced_channels.remove(channel)
        self.syncLock.release()

    def _rsync_channel(self, channel, timeout, _logInit=True):
        name = self._recvq(
            'sync//%s' % channel,
            decode=True,
            timeout=timeout,
            _logInit=_logInit
        )
        self.syncLock.acquire()
        self.synced_channels.add(name)
        self.syncLock.release()
        return name

    def send(self, msg, channel='__rsa__'):
        self.sendRSA(msg, channel)

    def sendRSA(self, msg, channel='__rsa__', sign='SHA-256'):
        self._ss_log("Preparing to send RSA encrypted message", "DEBUG")
        if type(msg) == str:
            msg = msg.encode()
        elif type(msg) != bytes:
            self._ss_log(
                "Attempt to send RSA message which was not str or bytes",
                "WARN"
            )
            raise TypeError("msg argument must be str or bytes")
        chunks = int(len(msg)/self.maxsize)
        if chunks < len(msg)/self.maxsize:
            chunks += 1
        self._ss_log("Sending message chunk size", "DETAIL")
        channel = self._sync_channel(channel)
        self._ss_log(
            "Reserved channel %s for this communication" % channel,
            "DEBUG"
        )
        self._sendq(self._baseEncrypt('%x' % chunks), channel)
        for i in range(chunks):
            self._ss_log("Sending chunk %d/%d" % (i, chunks), "DETAIL")
            self._sendq(rsa.encrypt(
                msg[self.maxsize*i:self.maxsize*(i+1)],
                self.rpub
            ), channel)
        self._ss_log("Message sent", "DEBUG")
        if sign:
            if sign not in rsa.pkcs1.HASH_METHODS:
                raise ValueError(
                    "Valid signature algorithms: " + str(
                        list(rsa.pkcs1.HASH_METHODS)
                    )
                )
            self._ss_log("Sending RSA signature", "DEBUG")
            self._sendq(
                self._baseEncrypt(rsa.sign(msg, self.priv, sign)),
                channel
            )
        else:
            self._sendq(
                self._baseEncrypt('-'),
                channel
            )
        self._desync_channel(channel)

    def recv(self, channel='__rsa__', decode=False, timeout=-1):
        return self.recvRSA(channel, decode, timeout)

    def recvRSA(self, channel='__rsa__', decode=False, timeout=-1):
        if timeout == -1:
            timeout = self.timeout
        self._ss_log("Waiting to receive an RSA encrypted message", "DEBUG")
        channel = self._rsync_channel(channel, timeout)
        self._ss_log(
            "Reserved channel %s for this communication" % channel,
            "DEBUG"
        )
        chunks = int(self._baseDecrypt(self._recvq(
            channel,
            timeout=timeout
        )).decode(), 16)
        msg = b""
        for i in range(chunks):
            self._ss_log("Receiving chunk %d/%d" % (i, chunks), "DETAIL")
            msg += rsa.decrypt(
                self._recvq(channel, timeout=timeout),
                self.priv
            )
        self._ss_log("Message received", "DEBUG")
        self._ss_log("Waiting for signature", "DETAIL")
        signature = self._baseDecrypt(self._recvq(channel, timeout=timeout))
        if signature != b'-':
            rsa.verify(
                msg,
                signature,
                self.rpub
            )
        else:
            self._ss_log(
                "No RSA signature received. Unable to verify message",
                "WARN"
            )
        if decode:
            msg = msg.decode()
        self._desync_channel(channel)
        return msg

    def sendAES(self, msg, channel='__aes__', key=False, iv=False):
        self._ss_log("Preparing to send AES encrypted message", "DEBUG")
        if type(msg) == str:
            msg = msg.encode()
        if key is True:
            key = rsa.randnum.read_random_bits(256)
        if type(key) != bytes and key is not False:
            self._ss_log("Key argument was neither True nor bytes", "WARN")
            raise TypeError("key must be either True or a bytes object")
        if iv is True:
            iv = rsa.randnum.read_random_bits(128)
        if type(iv) != bytes and iv is not False:
            self._ss_log("IV argument was neither True nor bytes", "WARN")
            raise TypeError("iv must be either True or a bytes object")
        # if key and iv are false, then encrypt using the base cipher
        if not (key or iv):
            mode = 'BASE'
            cipher = self.baseCipher
        # if key is true or a bytestring and iv is false, use AES ECB
        elif not iv:
            mode = 'ADV'
            cipher = Cipher.EncryptionCipher(
                key,
                secondary_cipher_type=AES.MODE_ECB,
                use_legacy_ciphers=True,
                legacy_store_nonce=False,
                legacy_randomized_nonce=False
            )
        # if both key and iv are either true or bytestrings, use AES EAX
        else:
            mode = 'ADV'
            cipher = Cipher.EncryptionCipher(
                key,
                iv,
                cipher_type=AES.MODE_EAX,
                store_nonce=True
            )
        self._ss_log(
            "Informing the remote socket to use AES encryption mode: "+mode,
            "DETAIL"
        )
        channel = self._sync_channel(channel)
        self._ss_log(
            "Reserved channel %s for this communication" % channel,
            "DEBUG"
        )
        self._sendq(self._baseEncrypt(mode), channel)
        if key:
            self._ss_log("Sending cipher key", "DETAIL")
            self.sendRSA(key, channel, 'MD5')
        if isinstance(msg, (BytesIO, BufferedReader)):
            self._ss_log("Sending message from file", "DEBUG")
            intake = msg.read(4096)
            while len(intake):
                if mode == 'BASE':
                    intake = protocols.padstring(intake)
                self._sendq(self._baseEncrypt('+'), channel)
                self._sendq(cipher.encrypt(intake), channel)
                intake = msg.read(4096)
            self._sendq(self._baseEncrypt('-'), channel)
        else:
            if type(msg) != bytes:
                self._ss_log(
                    "Attempt to send a message which was neither str, "
                    "bytes, or an open file",
                    "WARN"
                )
                raise TypeError("msg argument must be str or bytes")
            self._ss_log("Sending message from text", "DEBUG")
            self._sendq(self._baseEncrypt('+'), channel)
            if mode == 'BASE':
                msg = protocols.padstring(msg)
            self._sendq(cipher.encrypt(msg), channel)
            self._sendq(self._baseEncrypt('-'), channel)
        self._ss_log("Message sent", "DEBUG")
        if mode != 'BASE':
            self._ss_log("Sending EAX digest", "DETAIL")
            self._sendq(cipher.finish(), channel)
        self._desync_channel(channel)

    def recvAES(
        self,
        channel='__aes__',
        decode=False,
        timeout=-1,
        output_file=None,
        _logInit=True
    ):
        if _logInit:
            self._ss_log(
                "Attempting to receive AES encrypted message",
                "DEBUG"
            )
        if timeout == -1:
            timeout = self.timeout
        channel = self._rsync_channel(channel, timeout, _logInit=_logInit)
        self._ss_log(
            "Reserved channel %s for this communication" % channel,
            "DEBUG"
        )
        if not _logInit:
            timeout = 0.5
        try:
            mode = self._baseDecrypt(self._recvq(
                channel,
                timeout=timeout,
                _logInit=_logInit
            )).decode()
            self._ss_log("AES encryption using mode: "+mode, "DETAIL")
            cipher = None
            if mode == 'BASE':
                cipher = self.baseCipher
            elif mode == 'ECB':
                self._ss_log("Receiving cipher key", "DETAIL")
                cipher = AES.new(
                    self.recvRSA(channel, timeout=timeout),
                    AES.MODE_ECB
                )
            elif mode == 'CBC':
                self._ss_log("Receiving cipher key", "DETAIL")
                cipher = AES.new(
                    self.recvRSA(channel, timeout=timeout),
                    AES.MODE_CBC,
                    iv=rsa.randnum.read_random_bits(128)
                )
                cipher.decrypt(self._recvq(channel, timeout=timeout))
            elif mode == 'ADV':
                self._ss_log("Receiving cipher key", "DETAIL")
                key = self.recvRSA(channel, timeout=timeout)
                cipher = None
            else:
                raise ValueError("Unsupported Cipher type: "+mode)
            writer = None
            if type(output_file) == str:
                self._ss_log("Output will be written to file", "DEBUG")
                writer = open(output_file, mode='wb')
            elif isinstance(output_file, (BytesIO, BufferedWriter)):
                self._ss_log("Output will be written to file", "DEBUG")
                writer = output_file
            command = self._baseDecrypt(self._recvq(channel, timeout=timeout))
            msg = b""
            while command == b'+':
                self._ss_log("Receiving chunk", "DETAIL")
                intake = self._recvq(
                    channel,
                    timeout=timeout
                )
                if mode == 'ADV' and cipher is None:
                    cipher = Cipher.DecryptionCipher(
                        intake,
                        key=key
                    )
                    intake = cipher.decrypt(b'')
                else:
                    intake = cipher.decrypt(intake)
                    if mode != 'ADV':
                        intake = protocols.unpadstring(intake)
                if writer is not None:
                    writer.write(intake)
                else:
                    msg += intake
                command = self._baseDecrypt(self._recvq(
                    channel,
                    timeout=timeout
                ))
            self._ss_log("Payload received", "DEBUG")
            if mode == 'ADV':
                self._ss_log("Waiting for digest digest", "DETAIL")
                digest = self._recvq(channel, timeout=timeout)
                if writer is not None:
                    writer.write(cipher.decrypt(digest) + cipher.finish())
                else:
                    msg += cipher.decrypt(digest) + cipher.finish()
                self._ss_log("Message digest successful", "DETAIL")
            self._desync_channel(channel)
            if writer is not None:
                writer.close()
                return writer.name
            if decode:
                msg = msg.decode()
            return msg
        except socketTimeout:
            raise socketTimeout()

    def sendRAW(self, msg, channel='__raw__'):
        if type(msg) == str:
            msg = msg.encode()
        elif type(msg) != bytes:
            self._ss_log(
                "Attempt to send RAW message which was neither str nor bytes",
                "WARN"
            )
            raise TypeError("msg argument must be str or bytes")
        self._ss_log("Sending unencrypted message", "DEBUG")
        self._sendq(msg, channel)

    def recvRAW(self, channel='__raw__', decode=False, timeout=-1):
        if timeout == -1:
            timeout = self.timeout
        self._ss_log("Waiting to receive unencrypted message", "DEBUG")
        return self._recvq(channel, decode, timeout)

    def settimeout(self, timeout):
        self.timeout = timeout

    def gettimeout(self):
        return self.timeout

    def close(self):
        self._ss_log("SecureSocket closing connection")
        super().close()
        self._ss_log.close()
