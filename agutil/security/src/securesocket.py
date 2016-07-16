from .. import _PROTOCOL_IDENTIFIER_ as _protocol
from ... import io
import hashlib
import rsa
import os
import Crypto.Cipher.AES as AES
import pickle
import threading
import shutil
from io import BytesIO
from . import protocols

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
                    hashlib.sha512(initPassword.encode()+b"lol").hexdigest().encode()
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
        self._sendq(self._baseEncrypt(pickle.dumps(self.pub)), '__control__')
        self.rpub = pickle.loads(self._baseDecrypt(self._recvq('__control__')))
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

    def send(self, msg, channel='__rsa__', retries=1):
        self.sendRSA(msg, channel, retries)

    def sendRSA(self, msg, channel='__rsa__', retries=1):
        if type(msg)==str:
            msg=msg.encode()
        elif type(msg)!=bytes:
            raise TypeError("msg argument must be str or bytes")
        chunks = int(len(msg)/self.maxsize)
        if chunks < len(msg)/self.maxsize:
            chunks += 1
        self._sendq(self._baseEncrypt('%x'%retries), channel)
        for attempt in range(retries):
            self._sendq(self._baseEncrypt('%x'%chunks), channel)
            for i in range(chunks):
                self._sendq(rsa.encrypt(
                    msg[self.maxsize*i:self.maxsize*(i+1)],
                    self.rpub
                ), channel)
            self._sendq(hashlib.sha512(msg).hexdigest(), channel)
            if self._baseDecrypt(self._recvq(channel, timeout=(self.timeout+2 if self.timeout!=None else None))) == b'OK':
                return
        raise IOError("Unable to encrypt and send message over channel %s in %d retries" %(channel, retries))

    def recv(self, channel='__rsa__', decode=False, timeout=-1):
        return self.recvRSA(channel, decode, timeout)

    def recvRSA(self, channel='__rsa__', decode=False, timeout=-1):
        if timeout == -1:
            timeout = self.timeout
        retries = int(self._baseDecrypt(self._recvq(channel, timeout=timeout)).decode(), 16)
        for attempt in range(retries):
            chunks = int(self._baseDecrypt(self._recvq(channel, timeout=timeout)).decode(), 16)
            msg = b""
            for i in range(chunks):
                msg += rsa.decrypt(
                    self._recvq(channel, timeout=timeout),
                    self.priv
                )
            hashcode = self._recvq(channel, True, timeout)
            if hashcode == hashlib.sha512(msg).hexdigest():
                self._sendq(self._baseEncrypt('OK'), channel)
                if decode:
                    msg = msg.decode()
                return msg
            self._sendq(self._baseEncrypt('FAIL'), channel)
        raise IOError("Unable to receive and decrypt message over channel %s in %d retries" %(channel, retries))

    def sendAES(self, msg, channel='__aes__', key=False, iv=False):
        if type(msg)==str:
            msg=msg.encode()
        if key == True:
            key = rsa.randnum.read_random_bits(256)
        if type(key)!=bytes:
            raise TypeError("key must be either True or a bytes object")
        if iv == True:
            iv = rsa.randnum.read_random_bits(128)
        if type(iv)!=bytes:
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
        if isinstance(msg, BytesIO):
            intake = msg.read(4095)
            while len(intake):
                self._sendq(self._baseEncrypt('+'), channel)
                self._sendq(cipher.encrypt(protocols.padstring(intake)), channel)
                intake = msg.read(4095)
            self._sendq(self._baseEncrypt('-'), channel)
        else:
            if type(msg)!=bytes:
                raise TypeError("msg argument must be str or bytes")
            self._sendq(self._baseEncrypt('+'), channel)
            self._sendq(cipher.encrypt(protocols.padstring(msg)), channel)
            self._sendq(self._baseEncrypt('-'), channel)

    def recvAES(self, channel='__aes__', decode=False, timeout=-1, output_file=None):
        if timeout == -1:
            timeout = self.timeout
        mode = self._baseDecrypt(self._recvq(channel, timeout=timeout))
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
        elif isinstance(output_file, BytesIO):
            writer = output_file
        command = self._baseDecrypt(self._recvq(channel, timeout=timeout))
        msg = b""
        while command == b'+':
            intake = protocols.unpadstring(cipher.decrypt(self._recvq(channel, timeout=timeout)))
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
        msg = self._recvq(channel, decode, timeout)

    def settimeout(self, timeout):
        self.timeout = timeout

    def gettimeout(self):
        return self.timeout

    def close(self):
        super().close()


class SecureSocket_predecessor:
    def __init__(self, address, port, initPassword=None, defaultbits=4096, verbose=False, console=False, _debug_keys=None):
        _protocol_ = "<Agutil-security> <v1.0.0>"
        self._ready = False
        if address == 'listen' or address == '':
            #listen for connections
            if verbose:
                print("Awaiting an incoming connection...")
            ss = io.SocketServer(port, queue=0)
            self.sock = ss.accept()
            initiator = False
            ss.close()
        else:
            self.sock = io.Socket(address, port)
            initiator = True
        self.port = port
        self.defaultbits = defaultbits
        self.v = verbose
        if type(initPassword)!=str and type(initPassword)!=type(None):
            self.sock.close()
            raise TypeError("Password argument must be of type str or None")
        if initiator:
            protocolstring = _protocol_
            if initPassword!=None:
                protocolstring = _protocol_+" <password-%s>"%(
                    hashlib.sha512(
                        hashlib.sha512(initPassword.encode()+b"lol").hexdigest().encode()
                    ).hexdigest()
                )
            self.sock.send(protocolstring)
            response = self.sock.recv().decode()
            if response!='OK':
                self.sock.close()
                raise ValueError("The remote socket rejected this connection's identifier (Theirs: %s) (Ours: %s)"%(response, protocolstring))
        else:
            protocolstring = _protocol
            if initPassword!=None:
                protocolstring = _protocol+" <password-%s>"%(
                    hashlib.sha512(
                        hashlib.sha512(initPassword.encode()+b"lol").hexdigest().encode()
                    ).hexdigest()
                )
            remoteprotocol = self.sock.recv().decode()
            if protocolstring != remoteprotocol:
                self.sock.send(protocolstring)
                self.sock.close()
                raise ValueError("The remote socket provided an invalid identifier (Theirs: %s) (Ours: %s)"%(remoteprotocol, protocolstring))
            self.sock.send('OK')

        #now generate the base 1024-bit rsa key
        if self.v:
            print("Generating base 1024-bit rsa key")
        if _debug_keys != None:
            self.pub = _debug_keys[0]
            self.priv = _debug_keys[1]
            self.debugging = True
            if self.v:
                print("Skipping base key generation")
        else:
            (self.pub, self.priv) = rsa.newkeys(1024, True, RSA_CPU)
            self.debugging = False

        if initPassword!=None:
            self.baseCipher = AES.new(hashlib.sha256(initPassword.encode()).digest())
        else:
            self.baseCipher = _dummyCipher()

        if self.v:
            print("Exchanging base keys with the remote socket")
        self.sock.send(self.baseCipher.encrypt(protocols.padstring(pickle.dumps(self.pub))))
        self.remotePub = pickle.loads(protocols.unpadstring(self.baseCipher.decrypt(self.sock.recv())))

        self.sock.send(rsa.encrypt(
            b'OK',
            self.remotePub
        ))
        response = rsa.decrypt(
            self.sock.recv(),
            self.priv
        )
        if response != b'OK':
            raise ValueError("Error confirming encryption with the remote socket")

        self.channels = {}
        self.actionqueue = []
        self.actionlock = threading.Condition()
        self._shutdown = False
        self._thread = threading.Thread(target=protocols._SocketWorker, args=(self,), name="Worker thread", daemon=True)
        self._thread.start()
        self._ready =True
        self.defaultlock = threading.Condition()
        if initiator:
            self.init_thread = threading.Thread(target=SecureSocket.new_channel, args=(self, '_default_'), name="Initializer thread", daemon=True)
            self.init_thread.start()
        elif self.v:
            print("Waiting for the remote socket to open the default channel...")
        self.defaultlock.acquire()
        self.defaultlock.wait()
        self.defaultlock.release()
        if initiator:
            self.init_thread.join()

    def new_channel(self, name, rsabits=-1, mode='text', _initiator=True):
        if name in self.channels:
            raise KeyError("Channel name '%s' already exists" % (name))
        if mode!='text' and mode!='files':
            raise ValueError("Mode must be 'text' or 'files'")
        if rsabits == -1:
            rsabits = self.defaultbits
        if self.v:
            print("Opening a new channel '%s'" %(name))
            print("Generating a new %d-bit key.  (This may take a while)"%(rsabits))

        if self.debugging:
            _pub = self.pub
            _priv = self.priv
            if self.v:
                print("Skipping channel key generation")
        else:
            (_pub, _priv) = rsa.newkeys(rsabits, True, RSA_CPU)

        self.channels[name]= {
            'rsabits': rsabits,
            'mode': mode,
            'pub': _pub,
            'priv': _priv,
            'input': [],
            'output': [],
            'signatures':[],
            'hashes':[],
            'datalock': threading.Condition(),
            'notify': self.v,
            '_confirmed': not _initiator
        }
        if _initiator:
            self.channels[name]['datalock'].acquire()
            self.actionlock.acquire()
            if self.v:
                print("Securing the channel with the remote socket... (this may take a while)")
            self.actionqueue.append(protocols._NEW_CHANNEL_CMD%(
                name,
                rsabits,
                mode
            ))
            self.actionlock.release()
            self.channels[name]['datalock'].wait()
            self.channels[name]['datalock'].release()

    def close_channel(self, name):
        if name not in self.channels:
            raise KeyError("Channel name '%s' not opened" %(name))
        self.actionlock.acquire()
        self.actionqueue.append(protocols._CLOSE_CHANNEL_CMD%(name))
        self.actionlock.release()

    def _channel_confirmed(self, channel):
        if channel not in self.channels:
            return False
        return self.channels[channel]['_confirmed']

    def disconnect(self, notify=True):
        if not self._ready:
            try:
                self.sock.close()
            except AttributeError:
                pass
            return
        self._ready = False
        self.actionlock.acquire()
        self._shutdown = True
        self.actionqueue = []
        self.actionlock.release()
        if notify:
            if self.v:
                print("Disconnecting from the remote socket")
            self.sock.send(rsa.encrypt(b'<disconnect>', self.remotePub))
        self.sock.close()
        once = False
        for channel in self.channels:
            if self.channels[channel]['mode']=='files':
                self.channels[channel]['datalock'].acquire()
                if len(self.channels[channel]['input']):
                    if self.v and not once:
                        print("Cleaning up leftover files")
                        once = True
                    for filepath in self.channels[channel]['input']:
                        os.remove(filepath)
                self.channels[channel]['datalock'].release()
        self._thread.join()


    def close(self):
        self.disconnect()

    def __del__(self):
        self.disconnect()

    def send(self, payload, channel="_default_"):
        if channel not in self.channels:
            raise KeyError("Channel name '%s' not opened" %(channel))
        if self.channels[channel]['mode']=='text':
            self._text_out(payload, channel)
        elif self.channels[channel]['mode']=='files':
            self._file_out(payload, channel)

    def sendfile(self, filepath, channel="_default_file_"):
        if channel not in self.channels:
            if channel=="_default_file_":
                self.new_channel("_default_file_", mode="files")
            else:
                raise KeyError("Channel name '%s' not opened" %(channel))
        self.send(filepath, channel)

    def read(self, channel="_default_"):
        if channel not in self.channels:
            raise KeyError("Channel name '%s' not opened" %(channel))
        if self.channels[channel]['mode']=='text':
            return self._text_in(channel)

    def savefile(self, filepath, channel="_default_file_"):
        if channel not in self.channels:
            if channel=="_default_file_":
                if self.v:
                    print("Waiting for the remote socket to open the default file channel")
                self.defaultlock.acquire()
                self.defaultlock.wait()
                self.defaultlock.release()
            else:
                raise KeyError("Channel name '%s' not opened" %(channel))
        if self.channels[channel]['mode']=='files':
            return self._file_in(channel, filepath)

    def _text_out(self, message, channel):
        signature = rsa.sign(
            message.encode(),
            self.channels[channel]['priv'],
            'SHA-256'
        )
        rsa.verify(
            message.encode(),
            signature,
            self.channels[channel]['pub']
        )
        payload = rsa.encrypt(
            message.encode(),
            self.channels[channel]['rpub']
        )
        self.channels[channel]['datalock'].acquire()
        self.actionlock.acquire()
        self.channels[channel]['output'].append(payload)
        self.channels[channel]['signatures'].append(signature)
        self.actionqueue.append(protocols._TEXT_PAYLOAD_CMD%(channel))
        self.actionlock.release()
        self.channels[channel]['datalock'].release()

    def _text_in(self, channel):
        self.channels[channel]['datalock'].acquire()
        self.channels[channel]['datalock'].wait_for(lambda :len(self.channels[channel]['input']))
        raw = self.channels[channel]['input'].pop(0)
        sig = self.channels[channel]['hashes'].pop(0)
        self.channels[channel]['datalock'].release()
        msg = rsa.decrypt(
            raw,
            self.channels[channel]['priv']
        )
        rsa.verify(msg, sig, self.channels[channel]['rpub'])
        return msg.decode()

    def _file_out(self, filepath, channel):
        filepath = os.path.abspath(filepath)
        reader = open(filepath, mode='rb')
        intake = reader.read(4096)
        reader.close()
        signature = rsa.sign(
            intake,
            self.channels[channel]['priv'],
            'SHA-256'
        )
        rsa.verify(
            intake,
            signature,
            self.channels[channel]['pub']
        )
        self.channels[channel]['datalock'].acquire()
        self.actionlock.acquire()
        self.channels[channel]['output'].append(filepath)
        self.channels[channel]['signatures'].append(signature)
        self.actionqueue.append(protocols._FILE_PAYLOAD_CMD%(channel))
        self.actionlock.release()
        self.channels[channel]['datalock'].release()

    def _file_in(self, channel, destination=None):
        self.channels[channel]['datalock'].acquire()
        self.channels[channel]['datalock'].wait_for(lambda :len(self.channels[channel]['input']))
        filepath = self.channels[channel]['input'].pop(0)
        sig = self.channels[channel]['hashes'].pop(0)
        self.channels[channel]['datalock'].release()
        reader = open(filepath, mode='rb')
        intake = reader.read(4096)
        reader.close()
        rsa.verify(intake, sig, self.channels[channel]['rpub'])
        if destination==None and self.v:
            print("A file has been downloaded on channel '%s'"%channel)
            print("The file's authenticity has been verified")
            destination = os.path.abspath(input("Path to save the downloaded file: "))
        shutil.copyfile(filepath, destination)
        os.remove(filepath)
        return destination

    def _remote_shutdown(self):
        self.shutdown_thread = threading.Thread(target=_remote_shutdown_worker, args=(self,), name='Shutdown thread')
        self.shutdownlock = threading.Condition()
        self.shutdownlock.acquire()
        self.shutdown_thread.start()

def _remote_shutdown_worker(self):
    self.shutdownlock.acquire()
    self.shutdownlock.release()
    if self.v:
        print("The remote socket has disconnected")
    self.disconnect(False)
