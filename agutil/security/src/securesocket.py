from .. import _PROTOCOL_IDENTIFIER_ as _protocol
from ... import io
import hashlib
import rsa
import os
import Crypto.Cipher.AES as AES
import threading
from io import BytesIO, BufferedReader, BufferedWriter
from . import protocols, files

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
    def __init__(self, socket, password=None, rsabits=4096, verbose=False, timeout=3):
        if not isinstance(socket, io.Socket):
            raise TypeError("socket argument must be of type agutil.io.Socket")
        super().__init__(socket, _debug=verbose)
        self.v = verbose
        self.rsabits = rsabits
        self.timeout = timeout
        protocolstring = _protocol
        if password!=None:
            protocolstring = _protocol+" <password-%s>"%(
                hashlib.sha512(
                    hashlib.sha512(password.encode()+b"lol").digest()
                ).hexdigest()
            )
            self.baseCipher = AES.new(hashlib.sha256(password.encode()).digest())
        else:
            self.baseCipher = _dummyCipher()
        if self.v:
            print("Sending protocol identifier")
        self._sendq(protocolstring, '__control__')
        if self.v:
            print("Receiving remote identifier")
        remoteprotocol = self._recvq('__control__', decode=True, timeout=timeout)
        if remoteprotocol != protocolstring:
            self.close()
            raise ValueError("The remote socket provided an invalid protocol identifier. (Theirs: %s) (Ours: %s)" % (
                remoteprotocol,
                protocolstring
            ))
        if self.v:
            print("Sending confirmation")
        self._sendq(self._baseEncrypt('OK'), '__control__')
        if self.v:
            print("Receving confirmation")
        if self._baseDecrypt(self._recvq('__control__', timeout=timeout)) != b'OK':
            self.close()
            raise ValueError("Unable to confirm base encryption with the remote socket.  Are you sure you entered the correct password?")
        if self.v:
            print("Sending RSA keysize")
        self._sendq(self._baseEncrypt(format(rsabits, 'x')), '__control__')
        if self.v:
            print("Receiving remote RSA keysize")
        self.remote_rsabits = int(self._baseDecrypt(self._recvq('__control__', timeout=timeout)).decode(), 16)
        self.maxsize = int((self.remote_rsabits / 8)) - 16
        if self.v:
            print("Generating keypair...")
        (self.pub, self.priv) = rsa.newkeys(rsabits, True, RSA_CPU)
        self._sendq(self._baseEncrypt(protocols.intToBytes(self.pub.n)), '__control__')
        self._sendq(self._baseEncrypt(protocols.intToBytes(self.pub.e)), '__control__')
        _n = protocols.bytesToInt(self._baseDecrypt(self._recvq('__control__')))
        _e = protocols.bytesToInt(self._baseDecrypt(self._recvq('__control__')))
        self.rpub = rsa.PublicKey(_n, _e)
        self._sendq(rsa.encrypt(
            b'OK',
            self.rpub
        ), '__control__')
        response = rsa.decrypt(
            self._recvq('__control__', timeout=timeout),
            self.priv
        )
        if response != b'OK':
            self.close()
            raise ValueError("Unable to confirm RSA encryption with the remote socket.")


    def _sendq(self, msg, channel='__orphan__'):
        super().send(msg, channel)

    def _recvq(self, channel='__orphan__', decode=False, timeout=None):
        return super().recv(channel, decode, timeout)

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
        if type(msg)==str:
            msg=msg.encode()
        elif type(msg)!=bytes:
            raise TypeError("msg argument must be str or bytes")
        chunks = int(len(msg)/self.maxsize)
        if chunks < len(msg)/self.maxsize:
            chunks += 1
        self._sendq(self._baseEncrypt('%x'%chunks), channel)
        for i in range(chunks):
            self._sendq(rsa.encrypt(
                msg[self.maxsize*i:self.maxsize*(i+1)],
                self.rpub
            ), channel)

    def recv(self, channel='__rsa__', decode=False, timeout=-1):
        return self.recvRSA(channel, decode, timeout)

    def recvRSA(self, channel='__rsa__', decode=False, timeout=-1):
        if timeout == -1:
            timeout = self.timeout
        chunks = int(self._baseDecrypt(self._recvq(channel, timeout=timeout)).decode(), 16)
        msg = b""
        for i in range(chunks):
            msg += rsa.decrypt(
                self._recvq(channel, timeout=timeout),
                self.priv
            )
        if decode:
            msg = msg.decode()
        return msg

    def sendAES(self, msg, channel='__aes__', key=False, iv=False):
        if type(msg)==str:
            msg=msg.encode()
        if key == True:
            key = rsa.randnum.read_random_bits(256)
        if type(key)!=bytes and key!=False:
            raise TypeError("key must be either True or a bytes object")
        if iv == True:
            iv = rsa.randnum.read_random_bits(128)
        if type(iv)!=bytes and iv!=False:
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
        self._sendq(self._baseEncrypt(mode), channel)
        if key:
            self.sendRSA(key, channel)
        if iv:
            # self._sendq(self._baseEncrypt('+'))
            self._sendq(cipher.encrypt(rsa.randnum.read_random_bits(128)), channel)
        if isinstance(msg, (BytesIO, BufferedReader)):
            intake = msg.read(4095)
            while len(intake):
                self._sendq(self._baseEncrypt('+'), channel)
                self._sendq(files._encrypt_chunk(intake, cipher), channel)
                intake = msg.read(4095)
            self._sendq(self._baseEncrypt('-'), channel)
        else:
            if type(msg)!=bytes:
                print(type(msg))
                raise TypeError("msg argument must be str or bytes")
            self._sendq(self._baseEncrypt('+'), channel)
            self._sendq(files._encrypt_chunk(msg, cipher), channel)
            self._sendq(self._baseEncrypt('-'), channel)

    def recvAES(self, channel='__aes__', decode=False, timeout=-1, output_file=None):
        if timeout == -1:
            timeout = self.timeout
        mode = self._baseDecrypt(self._recvq(channel, timeout=timeout)).decode()
        if mode == 'BASE':
            cipher = self.baseCipher
        elif mode == 'ECB':
            cipher = AES.new(self.recvRSA(channel, timeout=timeout))
        else:
            cipher = AES.new(self.recvRSA(channel, timeout=timeout), AES.MODE_CBC,rsa.randnum.read_random_bits(128))
            cipher.decrypt(self._recvq(channel, timeout=timeout))
        writer = None
        if type(output_file) == str:
            writer = open(output_file, mode='wb')
        elif isinstance(output_file, (BytesIO, BufferedWriter)):
            writer = output_file
        command = self._baseDecrypt(self._recvq(channel, timeout=timeout))
        msg = b""
        while command == b'+':
            intake = files._decrypt_chunk(self._recvq(channel, timeout=timeout), cipher)
            if writer != None:
                writer.write(intake)
            else:
                msg += intake
            command = self._baseDecrypt(self._recvq(channel, timeout=timeout))
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
            raise TypeError("msg argument must be str or bytes")
        self._sendq(msg, channel)

    def recvRAW(self, channel='__raw__', decode=False, timeout=-1):
        if timeout == -1:
            timeout = self.timeout
        return self._recvq(channel, decode, timeout)

    def settimeout(self, timeout):
        self.timeout = timeout

    def gettimeout(self):
        return self.timeout

    def close(self):
        super().close()
