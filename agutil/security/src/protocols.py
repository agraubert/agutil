import rsa
import os
import tempfile
import random
import shutil

_COMMANDS = ['kill', 'ti', 'to', 'fri', 'fro', 'fto', 'fti']
_CMD_LOOKUP = {}
#commands: {command code byte}{item name}{colon ':'}{item size (hex bytes)}{bar '|'}{item bytes}...
_CONSOLE = False

def lookupcmd(cmd):
    if cmd not in _CMD_LOOKUP:
        try:
            index = _COMMANDS.index(cmd)
            _CMD_LOOKUP[cmd] = index
        except ValueError:
            raise ValueError("Command \'%s\' not supported" %cmd)
    return _CMD_LOOKUP[cmd]

def parsecmd(cmd):
    data = {
        'cmd' : cmd[0]
    }
    cmd = cmd[1:]
    index = cmd.find(b':')
    while index != -1:
        item_size = int(cmd[index+1:cmd.find(b'|')], 16)
        data[cmd[:index].decode()] = cmd[index+3:index+item_size+3].decode()
        cmd = cmd[index+item_size+2:]
        index = cmd.find(b':')
    return data

def packcmd(cmd, data):
    cmd_index = lookupcmd(cmd)
    if cmd_index == -1:
        raise ValueError("Command \'%s\' not supported" % cmd)
    cmd_string = bytes.fromhex('%02x'%cmd_index)
    for key in data:
        cmd_string += key.encode()+b":"+format(len(data[key]), 'x').encode()+b"|"+data[key].encode()
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
    return _WORKERS[cmd]


def _text_in(sock,cmd,name):
    print("Text in task started", name)
    sock.sock.sendRAW('+', name)
    print("Receiving retry count")
    retries = int(sock.sock.recvAES(name, True), 16)
    for attempt in range(retries):
        print("Receving message")
        msg = sock.sock.recvRSA(name)
        print("Receiving signature")
        signature = sock.sock.recvRAW(name)
        try:
            print("Checking signature")
            rsa.verify(
                msg,
                signature,
                sock.sock.rpub
            )
            print("Sending confirmation")
            sock.sock.sendRAW('+', name)
            sock.intakelock.acquire()
            sock.queuedmessages.append(msg)
            sock.intakelock.notify_all()
            sock.intakelock.release()
            return
        except rsa.pkcs1.VerificationError:
            sock.sock.sendRAW('-', name)
    raise IOError("Background worker %s was unable to receive and decrypt the message in %d retries" % (name, retries))

def _text_out(sock,cmd,name):
    print("Text out task started", name)
    sock.sock.sendAES(packcmd(
        'ti',
        {'name':name}
    ), '__cmd__')
    print("Waiting to receive task confirmation")
    sock.sock.recvRAW(name, timeout=None)
    print("Sending retry count")
    sock.sock.sendAES(format(cmd['retries'], 'x'), name)
    for attempt in range(int(cmd['retries'])):
        print("Sending message")
        sock.sock.sendRSA(cmd['msg'], name)
        print("Sending signature")
        sock.sock.sendRAW(rsa.sign(
            cmd['msg'],
            sock.sock.priv,
            'SHA-256'
        ), name)
        print("Waiting for signature confirmation")
        if sock.sock.recvRAW(name, True) == '+':
            return
    raise IOError("Background worker %s was unable to encrypt and send the message in %d retries" % (name, int(cmd['retries'])))

def _file_request_out(sock,cmd,name):
    sock.authlock.acquire()
    auth_key = "".join(chr(random.randint(32, 255)) for _ in range(5))
    while auth_key in sock.filemap:
        auth_key = "".join(chr(random.randint(32, 255)) for _ in range(5))
    staging_location = tempfile.NamedTemporaryFile().name
    shutil.copyfile(cmd['filepath'], staging_location)
    sock.filemap[auth_key] = staging_location
    sock.authlock.release()
    sock.sock.sendAES(packcmd(
        'fri',
        {'auth':auth_key, 'filename':os.path.basename(cmd['filepath']), 'name':name}
    ), '__cmd__')

def _file_request_in(sock,cmd,name):
    sock.authlock.acquire()
    sock.authqueue.append((cmd['filename'], cmd['auth']))
    sock.authlock.notify_all()
    sock.authlock.release()

def _file_transfer_out(sock,cmd,name):
    sock.authlock.acquire()
    filepath = sock.filemap[cmd['auth']]
    del sock.filemap[cmd['auth']]
    sock.authlock.release()
    reader = open(filepath, mode='rb')
    sock.sock.sendRAW('+', name)
    sock.sock.sendAES(reader, name, True, True)
    os.remove(filepath)


def _file_transfer_in(sock,cmd,name):
    sock.sock.sendAES(packcmd(
        'fto',
        {'name':name, 'auth':cmd['auth']}
    ))
    sock.sock.recvRAW(name, timeout=None)
    sock.sock.recvAES(name, output_file=cmd['filepath'])
    sock.transferlock.acquire()
    sock.completed_transfers.add(cmd['filepath'])
    sock.transferlock.notify_all()
    sock.transferlock.release()

_WORKERS = {
    'ti' : _text_in,
    'to' : _text_out,
    'fri' : _file_request_in,
    'fro' : _file_request_out,
    'fti' : _file_transfer_in,
    'fto' : _file_transfer_out
}
