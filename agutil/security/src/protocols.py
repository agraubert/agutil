from socket import timeout, error
import rsa
import pickle
import hashlib
_NEW_CHANNEL_CMD = "<new-channel> <name|%s> <rsabits|%d> <mode|%s>"
_TEXT_PAYLOAD_CMD = "<payload> <channel|%s> <md5|%s> <signature|%s>"
_CONSOLE = False

def parsecmd(cmd):
    parts = [item[1:-1] for item in cmd.strip().split(' ')]
    output = {
        '_CMD_' : parts[0],
        '_RAW_' : ""+cmd
    }
    payload = []
    for i in range(1, len(parts)):
        index = parts[i].find('|')
        if index != -1:
            output[parts[i][:index]] = parts[i][index+1:]
        else:
            payload.append(parts[i])
    return (output, payload)

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
        else:
             tmp+=current.decode()
    size = int(tmp)
    return msg[len(tmp)+1:len(tmp)+1+size]

def _SocketWorker(_socket):
    while not _socket._shutdown:
        action = None
        _socket.actionlock.acquire()
        if len(_socket.actionqueue):
            action = _socket.actionqueue.pop(0)
            _socket.actionlock.release()
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
        if action!=None:
            args = parsecmd(action)



def _newChannel_init(_socket, cmd):
    _socket.sock.settimeout(None)
    _socket.send(rsa.encrypt(
        cmd['_RAW_'].encode(),
        _socket.remotePub
    ))
    response = rsa.decrypt(
        _socket.sock.recv(),
        _sock.priv
    ).decode()
    if response == 'BAD':
        raise KeyError("Channel name '%s' already exists on remote socket" % (cmd['name']))
    _socket.channels[cmd['name']]['rpub'] = pickle.loads(rsa.decrypt(
        _socket.sock.recv(),
        _socket.priv
    ))
    _socket.sock.send(rsa.encrypt(
        pickle.dumps(_socket.channels[cmd['name']]['pub']),
        _socket.remotePub
    ))


def _newChannel(_socket, cmd):
    _socket.sock.settimeout(None)
    try:
        _socket._new_channel_remote(
            cmd['name'],
            int(cmd['rsabits']),
            cmd['mode']
        )
    except KeyError:
        _socket.sock.send(rsa.encrypt(
            b'BAD',
            _socket.remotePub
        ))
        return
    _socket.sock.send(rsa.encrypt(
        pickle.dumps(_socket.channels[cmd['name']]['pub']),
        _socket.remotePub
    ))
    _socket.channels[cmd['name']]['rpub'] = pickle.loads(rsa.decrypt(
        _socket.sock.recv(),
        _socket.priv
    ))

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
        _socket.sock.send(_socket.channels[cmd['name']]['output'].pop(0))

def _text_payload(_socket, cmd):
    _socket.sock.settimeout(None)
    if cmd['channel'] in _socket.channels:
        _socket.sock.send(rsa.encrypt(
            b"OK",
            _socket.remotePub
        ))
        _socket.channels[cmd['channel']]['input'].append(_socket.sock.recv())
        if _socket.channels[cmd['channel']]['notify']:
            print("New message received on channel", cmd['channel'])
            if _CONSOLE:
                print("Type '!!FIX THIS MESSAGE!!' to decrypt and read message")
            else:
                print("Use the .read() method of this SecureSocket to decrypt and read this message")
