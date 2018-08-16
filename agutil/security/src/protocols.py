import rsa
import os
import random
from socket import timeout as socketTimeout

_COMMANDS = [
    'kill',
    'ti',
    'to',
    'fri',
    'fro',
    'fto',
    'fti',
    '_NULL',
    'dci',
    'TEXT',
    'FILE',
    'SHUTDOWN'
]
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
