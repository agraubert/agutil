from .. import _PROTOCOL_IDENTIFIER_ as _protocol
import hashlib
import rsa
import os
import Crypto.Cipher.AES as AES
import pickle
import threading

RSA_CPU = os.cpu_count()
if RSA_CPU == None:
    RSA_CPU = 2
RSA_CPU/=2

def padstring(msg):
    if type(msg)==str:
        msg = msg.encode()
    if type(msg)!=bytes:
        raise TypeError("msg must be type str or bytes")
    payload_size = len(msg)
    msg = str(payload_size).encode() + b'|' + msg
    return msg + bytes((16-len(msg))%16)

def unpadstring(msg):
    tmp = ""
    while not found_string:
        current = msg[len(tmp):len(tmp)+1]
        if current == b'|':
            break
        else tmp+=current.decode()
    size = int(tmp)
    return msg[len(tmp)+1:len(tmp)+1+size]


class _dummyCipher:
    def encrypt(self, msg):
        return msg

    def decrypt(self, msg):
        return msg

class TextChannel:
    pass

class FileChannel:
    pass

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

        self.sock.send(self.baseCipher.encrypt(padstring(pickle.dumps(self.pub))))
        self.remotePub = pickle.loads(unpadstring(self.baseCipher.decrypt(self.sock.recv())))

        self.channels = {}
        self.actionqueue = []
        self.actionlock = threading.Condition()
        self._thread = threading.thread(target=SocketWorker, args=(self,))
        self._thread.start()
        if initiator:
            self.new_channel('_default_')

    def new_channel(self, name, rsabits=4096, mode='text'):
        if name in self.channels:
            raise KeyError("Channel name '%s' already exists" % (name))

        # _ch = None
        # if mode=='text':
        #     _ch = TextChannel
        # elif mode=='files':
        #     _ch = FileChannel
        # else:
        #     raise ValueError("Mode must be 'text' or 'files'")
        # self.channels[name]= {
        #     'rsabits': rsabits,
        #     'mode': mode,
        #     'channel': _ch(rsabits, True)
        # }

    def send(self, payload, channel="_default_"):
        if channel not in self.channels:
            raise KeyError("Channel name '%s' not opened" %(channel))


def SocketWorker(_socket):
    pass
