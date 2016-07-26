from ... import io, Logger, DummyLog, intToBytes, bytesToInt
import hashlib
import rsa
import os
import Crypto.Cipher.AES as AES
from io import BytesIO, BufferedReader, BufferedWriter
from . import protocols, files

_SECURESOCKET_IDENTIFIER_ = '<agutil.security.securesocket:1.0.0>'

RSA_CPU = None
try:
    RSA_CPU = os.cpu_count()
    if RSA_CPU == None:
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

class SecureSocket(io.QueuedSocket):
    def __init__(self, socket, password=None, rsabits=4096, timeout=3, logmethod=DummyLog, _skipIdentifier=False, _useIdentifier=_SECURESOCKET_IDENTIFIER_):
        if isinstance(logmethod, Logger):
            self.sLog = logmethod.bindToSender("SecureSocket")
        else:
            self.sLog = logmethod
        if not isinstance(socket, io.Socket):
            raise TypeError("socket argument must be of type agutil.io.Socket")
        super().__init__(socket, logmethod=self.sLog.bindToSender(self.sLog.name+"->QueuedSocket"))
        self.sLog("The underlying QueuedSocket has been initialized.  Exchanging encryption data now")
        self.rsabits = rsabits
        if not (timeout==None or type(timeout)==int):
            raise TypeError("Timeout parameter must be an integer or None")
        if type(timeout)==int and timeout < 0:
            raise ValueError("Timeout cannot be negative")
        self.timeout = timeout
        protocolstring=_useIdentifier
        if password!=None:
            protocolstring+="<agutil.security.securesocket.password:%s>"%(
                hashlib.sha512(
                    hashlib.sha512(password.encode()+b"lol").digest()
                ).hexdigest()
            )
            self.baseCipher = AES.new(hashlib.sha256(password.encode()).digest())
        else:
            self.baseCipher = _dummyCipher()
        self.sLog("Sending protocol identifier", "DETAIL")
        self._sendq(protocolstring, '__protocol__')
        self.sLog("Receiving remote identifier", "DETAIL")
        remoteprotocol = self._recvq('__protocol__', decode=True, timeout=timeout)
        if remoteprotocol != protocolstring:
            self.sLog("The remote socket provided an invalid SecureSocket protocol identifier. (Theirs: %s) (Ours: %s)" % (
                remoteprotocol,
                protocolstring
            ), "WARN")
            self.close()
            raise ValueError("The remote socket provided an invalid protocol identifier at the SecureSocket level")
        self.sLog("Sending encryption confirmation", "DETAIL")
        self._sendq(self._baseEncrypt('OK'), '__control__')
        self.sLog("Receiving remote encryption confirmation", "DETAIL")
        if self._baseDecrypt(self._recvq('__control__', timeout=timeout)) != b'OK':
            self.sLog("Unable to confirm base encryption with the remote socket.  Are you sure you entered the correct password?", "WARN")
            self.close()
            raise ValueError("Unable to confirm base encryption with the remote socket.  Are you sure you entered the correct password?")
        self.sLog("Sending RSA keysize", "DETAIL")
        self._sendq(self._baseEncrypt(format(rsabits, 'x')), '__control__')
        self.sLog("Receiving remote RSA keysize", "DETAIL")
        self.remote_rsabits = int(self._baseDecrypt(self._recvq('__control__', timeout=timeout)).decode(), 16)
        self.maxsize = int((self.remote_rsabits / 8)) - 16
        self.sLog("Generation RSA keypair", "DEBUG")
        (self.pub, self.priv) = rsa.newkeys(rsabits, True, RSA_CPU)
        self.sLog("Sending RSA pubkey", "DETAIL")
        self._sendq(self._baseEncrypt(intToBytes(self.pub.n)), '__control__')
        self._sendq(self._baseEncrypt(intToBytes(self.pub.e)), '__control__')
        self.sLog("Receiving remote RSA pubkey", "DETAIL")
        _n = bytesToInt(self._baseDecrypt(self._recvq('__control__')))
        _e = bytesToInt(self._baseDecrypt(self._recvq('__control__')))
        self.rpub = rsa.PublicKey(_n, _e)
        self.sLog("Confirming encryption", "DEBUG")
        self._sendq(rsa.encrypt(
            b'OK',
            self.rpub
        ), '__control__')
        response = rsa.decrypt(
            self._recvq('__control__', timeout=timeout),
            self.priv
        )
        if response != b'OK':
            self.sLog("Unable to confirm RSA encryption with the remote socket.", "WARN")
            self.close()
            raise ValueError("Unable to confirm RSA encryption with the remote socket.")


    def _sendq(self, msg, channel='__orphan__'):
        super().send(msg, channel)

    def _recvq(self, channel='__orphan__', decode=False, timeout=None, _logInit=True):
        return super().recv(channel, decode, timeout, _logInit)

    def _baseEncrypt(self, msg):
        return self.baseCipher.encrypt(
            protocols.padstring(msg)
        )

    def _baseDecrypt(self, msg):
        return protocols.unpadstring(
            self.baseCipher.decrypt(msg)
        )

    def send(self, msg, channel='__rsa__'):
        self.sendRSA(msg, channel)

    def sendRSA(self, msg, channel='__rsa__'):
        self.sLog("Preparing to send RSA encrypted message", "DEBUG")
        if type(msg)==str:
            msg=msg.encode()
        elif type(msg)!=bytes:
            self.sLog("Attempt to send RSA message which was not str or bytes", "WARN")
            raise TypeError("msg argument must be str or bytes")
        chunks = int(len(msg)/self.maxsize)
        if chunks < len(msg)/self.maxsize:
            chunks += 1
        self.sLog("Sending message chunk size", "DETAIL")
        self._sendq(self._baseEncrypt('%x'%chunks), channel)
        for i in range(chunks):
            self.sLog("Sending chunk %d"%i, "DETAIL")
            self._sendq(rsa.encrypt(
                msg[self.maxsize*i:self.maxsize*(i+1)],
                self.rpub
            ), channel)
        self.sLog("Message sent", "DEBUG")

    def recv(self, channel='__rsa__', decode=False, timeout=-1):
        return self.recvRSA(channel, decode, timeout)

    def recvRSA(self, channel='__rsa__', decode=False, timeout=-1):
        if timeout == -1:
            timeout = self.timeout
        self.sLog("Waiting to receive an RSA encrypted message", "DEBUG")
        chunks = int(self._baseDecrypt(self._recvq(channel, timeout=timeout)).decode(), 16)
        msg = b""
        for i in range(chunks):
            self.sLog("Receiving chunk %d/%d" %(i, chunks), "DETAIL")
            msg += rsa.decrypt(
                self._recvq(channel, timeout=timeout),
                self.priv
            )
        self.sLog("Message received", "DEBUG")
        if decode:
            msg = msg.decode()
        return msg

    def sendAES(self, msg, channel='__aes__', key=False, iv=False):
        self.sLog("Preparing to send AES encrypted message", "DEBUG")
        if type(msg)==str:
            msg=msg.encode()
        if key == True:
            key = rsa.randnum.read_random_bits(256)
        if type(key)!=bytes and key!=False:
            self.sLog("Key argument was neither True nor bytes", "WARN")
            raise TypeError("key must be either True or a bytes object")
        if iv == True:
            iv = rsa.randnum.read_random_bits(128)
        if type(iv)!=bytes and iv!=False:
            self.sLog("IV argument was neither True nor bytes", "WARN")
            raise TypeError("iv must be either True or a bytes object")
        #if key and iv are false, then encrypt using the base cipher
        if not (key or iv):
            mode = 'BASE'
            cipher = self.baseCipher
        #if key is true or a bytestring and iv is false, use AES ECB
        elif not iv:
            mode = 'ECB'
            cipher = cipher = AES.new(key)
        #if both key and iv are either true or bytestrings, use AES CBC
        else:
            mode = 'CBC'
            cipher = AES.new(key, AES.MODE_CBC, iv)
        self.sLog("Informing the remote socket to use AES encryption mode: "+mode, "DETAIL")
        self._sendq(self._baseEncrypt(mode), channel)
        if key:
            self.sLog("Sending cipher key", "DETAIL")
            self.sendRSA(key, channel)
        if iv:
            # self._sendq(self._baseEncrypt('+'))
            self._sendq(cipher.encrypt(rsa.randnum.read_random_bits(128)), channel)
        if isinstance(msg, (BytesIO, BufferedReader)):
            self.sLog("Sending message from file", "DEBUG")
            intake = msg.read(4095)
            while len(intake):
                self._sendq(self._baseEncrypt('+'), channel)
                self._sendq(files._encrypt_chunk(intake, cipher), channel)
                intake = msg.read(4095)
            self._sendq(self._baseEncrypt('-'), channel)
        else:
            if type(msg)!=bytes:
                self.sLog("Attempt to send a message which was neither str, bytes, or an open file", "WARN")
                raise TypeError("msg argument must be str or bytes")
            self.sLog("Sending message from text", "DEBUG")
            self._sendq(self._baseEncrypt('+'), channel)
            self._sendq(files._encrypt_chunk(msg, cipher), channel)
            self._sendq(self._baseEncrypt('-'), channel)
        self.sLog("Message sent", "DEBUG")

    def recvAES(self, channel='__aes__', decode=False, timeout=-1, output_file=None, _logInit=True):
        if _logInit:
            self.sLog("Attempting to receive AES encrypted message", "DEBUG")
        if timeout == -1:
            timeout = self.timeout
        mode = self._baseDecrypt(self._recvq(channel, timeout=timeout, _logInit=_logInit)).decode()
        self.sLog("AES encryption using mode: "+mode, "DETAIL")
        if mode == 'BASE':
            cipher = self.baseCipher
        elif mode == 'ECB':
            self.sLog("Receiving cipher key", "DETAIL")
            cipher = AES.new(self.recvRSA(channel, timeout=timeout))
        else:
            self.sLog("Receiving cipher key", "DETAIL")
            cipher = AES.new(self.recvRSA(channel, timeout=timeout), AES.MODE_CBC,rsa.randnum.read_random_bits(128))
            cipher.decrypt(self._recvq(channel, timeout=timeout))
        writer = None
        if type(output_file) == str:
            self.sLog("Output will be written to file", "DEBUG")
            writer = open(output_file, mode='wb')
        elif isinstance(output_file, (BytesIO, BufferedWriter)):
            self.sLog("Output will be written to file", "DEBUG")
            writer = output_file
        command = self._baseDecrypt(self._recvq(channel, timeout=timeout))
        msg = b""
        while command == b'+':
            self.sLog("Receiving chunk", "DETAIL")
            intake = files._decrypt_chunk(self._recvq(channel, timeout=timeout), cipher)
            if writer != None:
                writer.write(intake)
            else:
                msg += intake
            command = self._baseDecrypt(self._recvq(channel, timeout=timeout))
        self.sLog("Payload received", "DEBUG")
        if writer != None:
            writer.close()
            return writer.name
        if decode:
            msg = msg.decode()
        return msg

    def sendRAW(self, msg, channel='__raw__'):
        if type(msg)==str:
            msg=msg.encode()
        elif type(msg)!=bytes:
            self.sLog("Attempt to send RAW message which was neither str nor bytes", "WARN")
            raise TypeError("msg argument must be str or bytes")
        self.sLog("Sending unencrypted message", "DEBUG")
        self._sendq(msg, channel)

    def recvRAW(self, channel='__raw__', decode=False, timeout=-1):
        if timeout == -1:
            timeout = self.timeout
        self.sLog("Waiting to receive unencrypted message", "DEBUG")
        return self._recvq(channel, decode, timeout)

    def settimeout(self, timeout):
        self.timeout = timeout

    def gettimeout(self):
        return self.timeout

    def close(self):
        self.sLog("SecureSocket closing connection")
        super().close()
        self.sLog.close()
