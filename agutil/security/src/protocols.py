from socket import timeout, error
import rsa
import pickle
import hashlib
_NEW_CHANNEL_CMD = "<new-channel> <name|%s> <rsabits|%d> <mode|%s>"
_TEXT_PAYLOAD_CMD = "<text-payload> <channel|%s>"
_CLOSE_CHANNEL_CMD = "<close-channel> <name|%s>"
_CONSOLE = False

def parsecmd(cmd):
    parts = [item[1:-1] for item in cmd.strip().split(' ')]
    output = {
        '_CMD_' : parts[0],
        '_RAW_' : ""+cmd
    }
    for i in range(1, len(parts)):
        index = parts[i].find('|')
        if index != -1:
            output[parts[i][:index]] = parts[i][index+1:]
    return output

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
    while True:
        current = msg[len(tmp):len(tmp)+1]
        if current == b'|':
            break
        else:
             tmp+=current.decode()
    size = int(tmp)
    return msg[len(tmp)+1:len(tmp)+1+size]

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
    _socket.channels[cmd['name']]['rpub'] = pickle.loads(
        unpadstring(_socket.baseCipher.decrypt(_socket.sock.recv()))
    )
    _socket.sock.send(
        _socket.baseCipher.encrypt(
            padstring(pickle.dumps(_socket.channels[cmd['name']]['pub']))
        )
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
    _socket.channels[cmd['name']]['confirmed'] = True
    _socket.channels[cmd['name']]['datalock'].notify_all()
    _socket.channels[cmd['name']]['datalock'].release()
    if cmd['name'] == '_default_' or cmd['name'] == '_default_file_':
        _socket.defaultlock.acquire()
        _socket.defaultlock.notify_all()
        _socket.defaultlock.release()


def _newChannel(_socket, cmd):
    _socket.sock.settimeout(None)
    try:
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
    if cmd['name'] == '_default_' or cmd['name'] == '_default_file_':
        _socket.defaultlock.acquire()
        _socket.defaultlock.notify_all()
        _socket.defaultlock.release()

def _text_payload_init(_socket, cmd):
    _socket.sock.settimeout(None)
    if cmd['channel'] in _socket.channels:
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