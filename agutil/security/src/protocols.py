from socket import timeout, error
import rsa
import pickle
import hashlib
import Crypto.Cipher.AES as AES
import os
import tempfile

_NEW_CHANNEL_CMD = "<new-channel> <name|%s> <rsabits|%d> <mode|%s>"
_TEXT_PAYLOAD_CMD = "<text-payload> <channel|%s>"
_FILE_PAYLOAD_CMD = "<file-payload> <channel|%s>"
_CLOSE_CHANNEL_CMD = "<close-channel> <name|%s>"
_COMMANDS = ['kill', 'ti', 'to', 'fri', 'fro', 'fti', 'fto']
_CMD_LOOKUP = {}
#commands: {command code byte}{item name}{colon ':'}{item size (hex bytes)}{bar '|'}{item bytes}...
_CONSOLE = False

def lookupcmd(cmd):
    if cmd not in _CMD_LOOKUP:
        index = _COMMANDS.find(cmd)
        if index == -1:
            raise ValueError("Command \'%s\' not supported" %cmd)
        _CMD_LOOKUP[cmd] = index
    return _CMD_LOOKUP[cmd]

def parsecmd(cmd):
    data['cmd'] = cmd[0]
    cmd = cmd[1:]
    index = cmd.find(b':')
    while index != -1:
        item_size = int(cmd[index+1:cmd.find(b'|')], 16)
        data[cmd[:index].decode()] = cmd[index+2:index+item_size+2]
        cmd = cmd[index+item_size+2:]
    return data

def packcmd(cmd, data):
    cmd_index = lookupcmd(cmd)
    if cmd_index == -1:
        raise ValueError("Command \'%s\' not supported" % cmd)
    cmd_string = format(cmd_index, 'x')
    for key in data:
        cmd_string += key+":"+format(len(data[key]), 'x')+"|"+data[key]
    return cmd_string

def padstring(msg):
    if type(msg)==str:
        msg = msg.encode()
    if type(msg)!=bytes:
        raise TypeError("msg must be type str or bytes")
    payload_size = len(msg)
    msg = format(payload_size, 'x').encode() + b'|' + msg
    return msg + bytes((16-len(msg))%16)

def unpadstring(msg):
    tmp = ""
    while True:
        current = msg[len(tmp):len(tmp)+1]
        if current == b'|':
            break
        else:
             tmp+=current.decode()
    size = int(tmp, 16)
    return msg[len(tmp)+1:len(tmp)+1+size]

def _assign_task(cmd):
    pass #return result from a lookup out of a cmd:function mapping table


def _text_in(sock,cmd,name):
    sock.sock.sendRAW('+', name)
    retries = int(sock.sock.recvAES(name, True), 16)
    for attempt in retries:
        msg = sock.sock.recvRSA(name)
        signature = sock.sock.recvAES(name, True)
        try:
            rsa.verify(
                msg,
                signature,
                sock.sock.rpub
            )
            sock.sock.sendRAW('+')
            return
        except rsa.pkcs1.VerificationError:
            sock.sock.sendRAW('-')
    raise IOError("Background worker %s was unable to receive and decrypt the message in %d retries" % (name, retries))

def _text_out(sock,cmd,name):
    sock.sock.sendAES(packcmd({
        'cmd':lookupcmd('ti'),
        'name':name
    }))
    sock.sock.recvRAW(name, timeout=None)
    sock.sock.sendAES(format(cmd['retries'], 'x'))
    for attempt in int(cmd['retries']):
        sock.sock.sendRSA(cmd['msg'], name)
        sock.sock.sendAES(rsa.sign(
            msg,
            sock.sock.priv,
            'SHA-256'
        ))
        if sock.sock.recvRAW(name, True) == '+':
            return
    raise IOError("Background worker %s was unable to encrypt and send the message in %d retries" % (name, int(cmd['retries'])))

def _file_request_out(sock,cmd,name):
    pass

def _file_request_in(sock,cmd,name):
    pass

def _file_transfer_out(sock,cmd,name):
    pass

def _file_transfer_in(sock,cmd,name):
    pass

def _SocketWorker(_socket):
    _socket.actionlock.acquire()
    while not _socket._shutdown:
        action = None
        starter = False
        if len(_socket.actionqueue):
            action = _socket.actionqueue.pop(0)
            _socket.actionlock.release()
            starter = True
        else:
            _socket.actionlock.release()
            _socket.sock.settimeout(.5)
            try:
                action = rsa.decrypt(
                    _socket.sock.recv(),
                    _socket.priv
                ).decode()
            except timeout:
                pass
            except OSError:
                _socket.sock.close()
                return
        if action!=None:
            args = parsecmd(action)
            if args['_CMD_'] == 'new-channel':
                if starter:
                    _newChannel_init(_socket, args)
                else:
                    _newChannel(_socket, args)
            elif args['_CMD_'] == 'text-payload':
                if starter:
                    _text_payload_init(_socket, args)
                else:
                    _text_payload(_socket, args)
            elif args['_CMD_'] == 'disconnect':
                _socket._remote_shutdown()
                _socket.shutdownlock.release()
            elif args['_CMD_'] == 'file-payload':
                if starter:
                    _file_payload_init(_socket, args)
                else:
                    _file_payload(_socket, args)

        #do stuff
        _socket.actionlock.acquire()

def _newChannel_init(_socket, cmd):
    _socket.sock.settimeout(None)
    _socket.sock.send(rsa.encrypt(
        cmd['_RAW_'].encode(),
        _socket.remotePub
    ))
    response = rsa.decrypt(
        _socket.sock.recv(),
        _socket.priv
    ).decode()
    if response == 'BAD':
        raise KeyError("Channel name '%s' already exists on remote socket" % (cmd['name']))
    _socket.sock.send(
        _socket.baseCipher.encrypt(
            padstring(pickle.dumps(_socket.channels[cmd['name']]['pub']))
        )
    )
    _socket.channels[cmd['name']]['rpub'] = pickle.loads(
        unpadstring(_socket.baseCipher.decrypt(_socket.sock.recv()))
    )
    _socket.sock.send(rsa.encrypt(
        b'OK',
        _socket.channels[cmd['name']]['rpub']
    ))
    response = rsa.decrypt(
        _socket.sock.recv(),
        _socket.channels[cmd['name']]['priv']
    )
    if response != b'OK':
        raise ValueError("Failed to confirm encryption on this channel")
    _socket.channels[cmd['name']]['datalock'].acquire()
    if _socket.v:
        print("Channel '%s' opened and secured"%(cmd['name']))
    _socket.channels[cmd['name']]['_confirmed'] = True
    _socket.channels[cmd['name']]['datalock'].notify_all()
    _socket.channels[cmd['name']]['datalock'].release()
    if cmd['name'] == '_default_' or cmd['name'] == '_default_file_':
        _socket.defaultlock.acquire()
        _socket.defaultlock.notify_all()
        _socket.defaultlock.release()


def _newChannel(_socket, cmd):
    _socket.sock.settimeout(None)
    try:
        if _socket.v:
            print("The remote socket has requested to open a new channel")
        _socket.new_channel(
            cmd['name'],
            int(cmd['rsabits']),
            cmd['mode'],
            False
        )
    except KeyError:
        _socket.sock.send(rsa.encrypt(
            b'BAD',
            _socket.remotePub
        ))
        return
    _socket.sock.send(rsa.encrypt(
        b'OK',
        _socket.remotePub
    ))
    _socket.channels[cmd['name']]['rpub'] = pickle.loads(
        unpadstring(_socket.baseCipher.decrypt(_socket.sock.recv()))
    )
    _socket.sock.send(
        _socket.baseCipher.encrypt(
            padstring(pickle.dumps(_socket.channels[cmd['name']]['pub']))
        )
    )
    response = rsa.decrypt(
        _socket.sock.recv(),
        _socket.channels[cmd['name']]['priv']
    )
    _socket.sock.send(rsa.encrypt(
        b'OK',
        _socket.channels[cmd['name']]['rpub']
    ))
    if response != b'OK':
        raise ValueError("Failed to confirm encryption on this channel")
    if _socket.v:
        print("Channel '%s' opened and secured"%(cmd['name']))
    if cmd['name'] == '_default_' or cmd['name']=='_default_file_':
        _socket.defaultlock.acquire()
        _socket.defaultlock.notify_all()
        _socket.defaultlock.release()

def _text_payload_init(_socket, cmd):
    _socket.sock.settimeout(None)
    if cmd['channel'] in _socket.channels and _socket.channels[cmd['channel']]['mode']=='text':
        _socket.sock.send(rsa.encrypt(
            cmd['_RAW_'].encode(),
            _socket.remotePub
        ))
        response = rsa.decrypt(
            _socket.sock.recv(),
            _socket.priv
        ).decode()
        if response != 'OK':
            raise KeyError("Channel name '%s' does not exist on remote socket" % (cmd['name']))
        _socket.channels[cmd['channel']]['datalock'].acquire()
        _socket.sock.send(_socket.channels[cmd['channel']]['signatures'].pop(0))
        _socket.sock.recv()
        _socket.sock.send(_socket.channels[cmd['channel']]['output'].pop(0))
        _socket.channels[cmd['channel']]['datalock'].release()

def _text_payload(_socket, cmd):
    _socket.sock.settimeout(None)
    if cmd['channel'] in _socket.channels:
        _socket.sock.send(rsa.encrypt(
            b"OK",
            _socket.remotePub
        ))
        sig = _socket.sock.recv()
        _socket.sock.send("continue")
        msg = _socket.sock.recv()
        _socket.channels[cmd['channel']]['datalock'].acquire()
        _socket.channels[cmd['channel']]['input'].append(msg)
        _socket.channels[cmd['channel']]['hashes'].append(sig)
        if _socket.channels[cmd['channel']]['notify']:
            print("New message received on channel", cmd['channel'])
            if _CONSOLE:
                print("Type '!!FIX THIS MESSAGE!!' to decrypt and read message")
            else:
                print("Use the .read() method of this SecureSocket to decrypt and read this message")
        _socket.channels[cmd['channel']]['datalock'].notify_all()
        _socket.channels[cmd['channel']]['datalock'].release()

def _file_payload_init(_socket, cmd):
    _socket.sock.settimeout(None)
    if cmd['channel'] in _socket.channels and _socket.channels[cmd['channel']]['mode']=='files':
        _socket.sock.send(rsa.encrypt(
            cmd['_RAW_'].encode(),
            _socket.remotePub
        ))
        response = rsa.decrypt(
            _socket.sock.recv(),
            _socket.priv
        ).decode()
        if response != 'OK':
            raise KeyError("Channel name '%s' does not exist on remote socket" % (cmd['name']))
        _socket.channels[cmd['channel']]['datalock'].acquire()
        signature = _socket.channels[cmd['channel']]['signatures'].pop(0)
        filepath = _socket.channels[cmd['channel']]['output'].pop(0)
        _socket.channels[cmd['channel']]['datalock'].release()
        aes_key = rsa.randnum.read_random_bits(256)
        aes_iv = rsa.randnum.read_random_bits(128)
        _socket.sock.send(rsa.encrypt(
            aes_key,
            _socket.channels[cmd['channel']]['rpub']
        ))
        _socket.sock.recv()
        _socket.sock.send(rsa.encrypt(
            aes_iv,
            _socket.channels[cmd['channel']]['rpub']
        ))
        cipher = AES.new(aes_key, AES.MODE_CBC, aes_iv)
        reader = open(filepath, mode='rb')
        _socket.sock.recv()
        intake = reader.read(4096)
        while len(intake)>0:
            _socket.sock.send(rsa.encrypt(
                b'payload',
                _socket.remotePub
            ))
            _socket.sock.recv()
            _socket.sock.send(cipher.encrypt(padstring(intake)))
            _socket.sock.recv()
            intake = reader.read(4096)
        _socket.sock.send(rsa.encrypt(
            b'end',
            _socket.remotePub
        ))
        reader.close()
        _socket.sock.recv()
        _socket.sock.send(signature)

def _file_payload(_socket, cmd):
    _socket.sock.settimeout(None)
    if cmd['channel'] in _socket.channels and _socket.channels[cmd['channel']]['mode']=='files':
        _socket.sock.send(rsa.encrypt(
            b'OK',
            _socket.remotePub
        ))
        aes_key = rsa.decrypt(
            _socket.sock.recv(),
            _socket.channels[cmd['channel']]['priv']
        )
        _socket.sock.send(b'continue')
        aes_iv = rsa.decrypt(
            _socket.sock.recv(),
            _socket.channels[cmd['channel']]['priv']
        )
        filepath = os.path.abspath(tempfile.NamedTemporaryFile().name)
        cipher = AES.new(aes_key, AES.MODE_CBC, aes_iv)
        writer = open(filepath, mode='wb')
        _socket.sock.send(b'continue')
        signal = rsa.decrypt(
            _socket.sock.recv(),
            _socket.priv
        )
        while signal == b'payload':
            _socket.sock.send(b'continue')
            writer.write(unpadstring(cipher.decrypt(_socket.sock.recv())))
            _socket.sock.send(b'continue')
            signal = rsa.decrypt(
                _socket.sock.recv(),
                _socket.priv
            )
            writer.flush()
        _socket.sock.send(b'continue')
        signature = _socket.sock.recv()
        writer.close()
        _socket.channels[cmd['channel']]['datalock'].acquire()
        _socket.channels[cmd['channel']]['input'].append(filepath)
        _socket.channels[cmd['channel']]['hashes'].append(signature)
        if _socket.channels[cmd['channel']]['notify']:
            print("New file received on channel", cmd['channel'])
            if _CONSOLE:
                print("Type '!!FIX THIS MESSAGE!!' to decrypt and read message")
            else:
                print("Use the .savefile() method of this SecureSocket to save this file")
        _socket.channels[cmd['channel']]['datalock'].notify_all()
        _socket.channels[cmd['channel']]['datalock'].release()
