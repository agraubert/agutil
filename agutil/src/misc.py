from itertools import chain, islice, zip_longest
from math import log

def intToBytes(num, padding_length=0):
    s = format(num, 'x')
    if len(s)%2:
        s = '0' + s
    result = bytes.fromhex(s)
    if len(result) < padding_length:
        return (bytes(padding_length-len(result)))+result
    return result

def bytesToInt(num):
    result = 0
    exp = int(256 ** (len(num)-1))
    for i in range(len(num)):
        result += int(num[i]*exp)
        exp //= 256
    return result

def split_iterable(seq, length):
    getter = iter(seq)
    while True:
        try:
            tmp = next(getter)
            yield chain([tmp], islice(getter, length-1))
        except StopIteration:
            return

def byte_xor(b1, b2):
    return intToBytes(bytesToInt(b1)^bytesToInt(b2), max(len(b1), len(b2)))

def byteSize(n):
    index = min(7, int(log(abs(n), 1024)))
    suffix = ['B', 'KiB', 'MiB', 'GiB', 'TiB', 'PiB', 'EiB', 'ZiB'][index]
    output = '%.1f'%(n / 1024**index)
    return output.rstrip('.0')+suffix
