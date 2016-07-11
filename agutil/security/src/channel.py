from .. import _PROTOCOL_IDENTIFIER_ as _protocol
import hashlib
import rsa
import os
import Crypto.Cipher.AES as AES
import pickle
import threading
from . import protocols

RSA_CPU = os.cpu_count()
if RSA_CPU == None:
    RSA_CPU = 2
RSA_CPU/=2

class _dummyCipher:
    def encrypt(self, msg):
        return msg

    def decrypt(self, msg):
        return msg

class SecureSocket:
    def __init__(self, socket, initiator=False, initPassword=None):
        if type(socket) != io.Socket:
            self.sock.close()
            raise TypeError("socket argument must be of type agutil.io.Socket")
        if type(initPassword)!=str and type(initPassword)!=type(None):
            self.sock.close()
            raise TypeError("Password argument must be of type str or None")
        self.sock = socket
        if initiator:
            protocolstring = _protocol
            if initPassword!=None:
                protocolstring = _protocol+" <password-%d>"%(
                    hashlib.sha512(
                        hashlib.sha512(initPassword.encode()+b"lol").hexdigest().encode()
                    ).hexdigest()
                )
            self.sock.send(protocolstring)
            response = self.sock.recv()
            if response!='OK':
                self.sock.close()
                raise ValueError("The remote socket rejected this connection's identifier")
        else:
            protocolstring = _protocol
            if initPassword!=None:
                protocolstring = _protocol+" <password-%d>"%(
                    hashlib.sha512(
                        hashlib.sha512(initPassword.encode()+b"lol").hexdigest().encode()
                    ).hexdigest()
                )
            remoteprotocol = self.sock.recv()
            if protocolstring != remoteprotocol:
                self.sock.send('BAD')
                self.sock.close()
                raise ValueError("The remote socket provided an invalid identifier")
            self.sock.send('OK')

        #now generate the base 1024-bit rsa key
        (self.pub, self.priv) = rsa.newkeys(1024, True, RSA_CPU)

        if initPassword!=None:
            self.baseCipher = AES.new(hashlib.sha256(initPassword.encode()).digest())
        else:
            self.baseCipher = _dummyCipher()

        self.sock.send(self.baseCipher.encrypt(protocols.padstring(pickle.dumps(self.pub))))
        self.remotePub = pickle.loads(protocols.unpadstring(self.baseCipher.decrypt(self.sock.recv())))

        self.channels = {}
        self.actionqueue = []
        self.actionlock = threading.Condition()
        self._thread = threading.thread(target=SocketWorker, args=(self,))
        self._thread.start()
        self._shutdown = False
        if initiator:
            self.new_channel('_default_')
            self.new_channel('_default_file_')

    def new_channel(self, name, rsabits=4096, mode='text'):
        if name in self.channels:
            raise KeyError("Channel name '%s' already exists" % (name))
        _ch = None
        if mode!='text' and mode!='files':
            raise ValueError("Mode must be 'text' or 'files'")
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
            'datalock': theading.Condition(),
            'notify': False
        }
        self.actionlock.acquire()
        self.actionqueue.append(protocols._NEW_CHANNEL_CMD%(
            name,
            rsabits,
            mode
        ))
        self.actionqueue.release()

    def close_channel(self, name):
        if name not in self.channels:
            raise KeyError("Channel name '%s' not opened" %(name))
        self.actionlock.acquire()
        self.actionqueue.append(protocols._CLOSE_CHANNEL_CMD%(name))
        self.actionlock.release()


    def disconnect(self):
        self.actionlock.acquire()
        self._shutdown = True
        self.actionqueue = []
        self.actionlock.release()
        self.sock.send(rsa.encrypt(b'<disconnect>', self.remotePub))
        self.sock.close()

    def __del__(self):
        self.disconnect()

    def send(self, payload, channel="_default_"):
        if channel not in self.channels:
            raise KeyError("Channel name '%s' not opened" %(channel))
        if self.channels[channel]['mode']=='text':
            self._text_out(payload, channel)

    def sendfile(self, filepath, channel="_default_file_"):
        self.send(filepath, channel)

    def read(self, channel="_default_"):
        if channel not in self.channels:
            raise KeyError("Channel name '%s' not opened" %(channel))
        if self.channels[channel]['mode']=='text':
            return self._text_in(channel)

    def savefile(self, filepath, channel="_default_file_"):
        pass

    def _text_out(self, message, channel):
        md5 = hashlib.md5(message.encode()).hexdigest()
        signature = rsa.sign(
            message.encode(),
            self.channels[channel]['priv'],
            'SHA-256'
        )
        payload = rsa.encrypt(
            message.encode(),
            self.channels[channel]['rpub']
        )
        self.channels[channel]['datalock'].acquire()
        self.actionlock.acquire()
        self.channels[channel]['output'].append(payload)
        self.channels[channel]['signatures'].append(signature)
        self.actionqueue.append(protocols._TEXT_PAYLOAD_CMD%(
            channel,
            md5
        ))
        self.actionlock.release()
        self.channels[channel]['datalock'].release()

    def _text_in(self, channel):
        self.channels[channel]['datalock'].acquire()
        self.channels[channel]['datalock'].wait_for(lambda :len(self.channels[channel]['input']))
        raw = self.channels[channel]['input'].pop(0)
        md5 = self.channels[channel]['hashes'].pop(0)
        self.channels[channel]['datalock'].release()
        msg = rsa.decrypt(
            raw,
            self.channels[channel]['priv']
        )
        if md5!=hashlib.md5(msg).hexdigest():
            raise ValueError("Hashcheck failed when receiving message")
        return msg.decode()
