from .. import _PROTOCOL_IDENTIFIER_ as _protocol
from ... import io
import hashlib
import rsa
import os
import Crypto.Cipher.AES as AES
import pickle
import threading
import shutil
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

class SecureSocket:
    def __init__(self, address, port, initPassword=None, defaultbits=4096, verbose=False, console=False, _debug_keys=None):
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
            protocolstring = _protocol
            if initPassword!=None:
                protocolstring = _protocol+" <password-%s>"%(
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
