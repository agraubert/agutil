from itertools import chain, islice, zip_longest

def intToBytes(num):
    s = format(num, 'x')
    if len(s)%2:
        s = '0' + s
    return bytes.fromhex(s)

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
    return intToBytes(bytesToInt(b1)^bytesToInt(b2))
