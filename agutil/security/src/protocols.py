import rsa
import os
import random
from socket import timeout as socketTimeout

_COMMANDS = ['kill', 'ti', 'to', 'fri', 'fro', 'fto', 'fti', '_NULL', 'dci', ]
_CMD_LOOKUP = {}
# commands: {command code byte}
# {item name}{colon ':'}{item size (hex bytes)}{bar '|'}{item bytes}...
_CONSOLE = False


def lookupcmd(cmd):
    if cmd not in _CMD_LOOKUP:
        try:
            index = _COMMANDS.index(cmd)
            _CMD_LOOKUP[cmd] = index
        except ValueError:
            raise ValueError("Command \'%s\' not supported" % cmd)
    return _CMD_LOOKUP[cmd]


def unpackcmd(cmd):
    _cmd_raw = b''+cmd
    data = {
        'cmd': cmd[0]
    }
    cmd = cmd[1:]
    index = cmd.find(b':')
    while index != -1:
        raw_size = cmd[index+1:cmd.find(b'|', index)]
        key = cmd[:index].decode()
        offset = len(raw_size)+2
        if raw_size == 0:
            data[key] = True
            item_size = 0
        else:
            item_size = int(raw_size, 16)
            data[key] = cmd[index+offset:index+item_size+offset].decode()
        cmd = cmd[index+item_size+offset:]
        index = cmd.find(b':')
    # print("UNPACK:", _cmd_raw,'-->', data)
    return data


def packcmd(cmd, data={}):
    cmd_index = lookupcmd(cmd)
    if cmd_index == -1:
        raise ValueError("Command \'%s\' not supported" % cmd)
    cmd_string = bytes.fromhex('%02x' % cmd_index)
    for key in data:
        if data[key] is True:
            data[key] = ''
        elif data[key] is False:
            continue
        if ':' in key:
            raise ValueError(
                "Command keys cannot contain ':' characters (ascii 58)"
            )
        cmd_string += ('%s:%x|%s' % (
            key,
            len(data[key].encode()),
            data[key]
        )).encode()
    # print("PACK:", cmd,":",data,'-->', cmd_string)
    return cmd_string


def padstring(msg):
    if type(msg) == str:
        msg = msg.encode()
    if type(msg) != bytes:
        raise TypeError("msg must be type str or bytes")
    padding_length = 16 - (len(msg) % 16)
    return (
        msg +
        os.urandom(padding_length-1) +
        bytes.fromhex('%02x' % padding_length)
    )


def unpadstring(msg):
    return msg[:-1*msg[-1]]


def _assign_task(cmd):
    return _WORKERS[cmd]


def _text_in(sock, cmd, name):
    sock.sock.sendRAW('+', name)
    tasklog = sock.log.bindToSender(sock.log.name+":"+name)
    tasklog("Initiated Text:in task", "DEBUG")
    retries = int(sock.sock.recvAES(name, True), 16)
    for attempt in range(retries):
        tasklog("Receving message and signature", "DEBUG")
        msg = sock.sock.recvRSA(name)
        signature = sock.sock.recvRAW(name)
        tasklog("Attempting to verify message signature", "DEBUG")
        try:
            rsa.verify(
                msg,
                signature,
                sock.sock.rpub
            )
            sock.sock.sendRAW('+', name)
            tasklog("Message validated", "DEBUG")
            sock.queuedmessages.append(msg)
            sock.intakeEvent.set()
            sock.schedulingqueue.append({
                'cmd': lookupcmd('kill'),
                'name': name
            })
            sock.pending_tasks.set()
            return
        except rsa.pkcs1.VerificationError:
            tasklog("Message failed signature validation", "WARN")
            sock.sock.sendRAW('-', name)
    tasklog("Exceded retry limit for inbound message.  Task aborted", "ERROR")
    sock.schedulingqueue.append({
        'cmd': lookupcmd('kill'),
        'name': name
    })
    sock.pending_tasks.set()
    raise IOError(
        "Background worker %s was unable to receive and "
        "decrypt the message in %d retries" % (
            name,
            retries
        )
    )


def _text_out(sock, cmd, name):
    tasklog = sock.log.bindToSender(sock.log.name+":"+name)
    tasklog("Scheduling Text:in on remote socket", "DEBUG")
    sock.sock.sendAES(packcmd(
        'ti',
        {'name': name}
    ), '__cmd__')
    sock.sock.recvRAW(name, timeout=None)
    tasklog("Initiated Text:out task", "DEBUG")
    sock.sock.sendAES(format(cmd['retries'], 'x'), name)
    for attempt in range(int(cmd['retries'])):
        tasklog("Sending message and signature", "DEBUG")
        sock.sock.sendRSA(cmd['msg'], name)
        sock.sock.sendRAW(rsa.sign(
            cmd['msg'],
            sock.sock.priv,
            'SHA-256'
        ), name)
        tasklog("Waiting for verification", "DETAIL")
        if sock.sock.recvRAW(name, True) == '+':
            tasklog("Message sent", "DEBUG")
            sock.schedulingqueue.append({
                'cmd': lookupcmd('kill'),
                'name': name
            })
            sock.pending_tasks.set()
            return
        tasklog("Remote socket was unable to validate the message", "WARN")
    tasklog("Exceded retry limit for outbound message.  Task aborted", "ERROR")
    sock.schedulingqueue.append({
        'cmd': lookupcmd('kill'),
        'name': name
    })
    sock.pending_tasks.set()
    raise IOError(
        "Background worker %s was unable to encrypt and "
        "send the message in %d retries" % (
            name,
            int(cmd['retries'])
        )
    )


def _file_request_out(sock, cmd, name):
    tasklog = sock.log.bindToSender(sock.log.name+":"+name)
    auth_key = "".join(chr(random.randint(32, 127)) for _ in range(5))
    while auth_key in sock.filemap:
        auth_key = "".join(chr(random.randint(32, 127)) for _ in range(5))
    sock.filemap[auth_key] = cmd['filepath']
    sock.sock.sendAES(packcmd(
        'fri',
        {
            'auth': auth_key,
            'filename': os.path.basename(cmd['filepath']),
            'name': name,
            'size': str(os.path.getsize(cmd['filepath']))
        }
    ), '__cmd__')
    tasklog("Sent file transfer request to remote socket", "DETAIL")
    sock.schedulingqueue.append({
        'cmd': lookupcmd('kill'),
        'name': name
    })
    sock.pending_tasks.set()


def _file_request_in(sock, cmd, name):
    tasklog = sock.log.bindToSender(sock.log.name+":"+name)
    tasklog("Received new file request.  Queueing authorization", "DETAIL")
    sock.authqueue.append((cmd['filename'], cmd['auth'], int(cmd['size'])))
    sock.pendingRequest.set()
    sock.schedulingqueue.append({
        'cmd': lookupcmd('kill'),
        'name': name
    })
    sock.pending_tasks.set()


def _file_transfer_out(sock, cmd, name):
    tasklog = sock.log.bindToSender(sock.log.name+":"+name)
    tasklog("Initiating File:out task", "DEBUG")
    filepath = sock.filemap[cmd['auth']]
    del sock.filemap[cmd['auth']]
    if 'reject' not in cmd:
        reader = open(filepath, mode='rb')
        tasklog("Now sending file to remote socket", "DETAIL")
        sock.sock.sendRAW('+', name)
        sock.sock.sendAES(reader, name, True, True)
        reader.close()
        tasklog("Transfer complete", "DEBUG")
    sock.schedulingqueue.append({
        'cmd': lookupcmd('kill'),
        'name': name
    })
    sock.pending_tasks.set()


def _file_transfer_in(sock, cmd, name):
    tasklog = sock.log.bindToSender(sock.log.name+":"+name)
    tasklog("Initiating File:in task", "DEBUG")
    sock.sock.sendAES(packcmd(
        'fto',
        {'name': name, 'auth': cmd['auth'], 'reject': 'reject' in cmd}
    ), '__cmd__')
    if 'reject' not in cmd:
        try:
            sock.sock.recvRAW(name, timeout=cmd['timeout'])
            tasklog("File transfer initiated", "DEBUG")
            sock.sock.recvAES(
                name,
                output_file=cmd['filepath'],
                timeout=cmd['timeout']
            )
        except socketTimeout:
            tasklog("Transfer timed out", "ERROR")
        else:
            tasklog("Transfer complete", "DEBUG")
            sock.completed_transfers.add(cmd['filepath'])
        finally:
            sock.transferTracking[cmd['key']].set()
    sock.schedulingqueue.append({
        'cmd': lookupcmd('kill'),
        'name': name
    })
    sock.pending_tasks.set()


def _disconnect_in(sock, cmd, name):
    from threading import Thread
    Thread(
        target=sock.close,
        args=(3, True),
        name="SecureConnection Shutdown Thread",
        daemon=True
    ).start()
    sock.schedulingqueue.append({
        'cmd': lookupcmd('kill'),
        'name': name
    })
    sock.pending_tasks.set()


_WORKERS = {
    'ti': _text_in,
    'to': _text_out,
    'fri': _file_request_in,
    'fro': _file_request_out,
    'fti': _file_transfer_in,
    'fto': _file_transfer_out,
    'dci': _disconnect_in
}
