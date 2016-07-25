from itertools import chain, islice, zip_longest
def split_iterable(seq, length):
    getter = iter(seq)
    while True:
        try:
            tmp = next(getter)
            yield chain([tmp], islice(getter, length-1))
        except StopIteration:
            return

def byte_xor(b1, b2):
    output = []
    for x, y in zip_longest(reversed(b1), reversed(b2), fillvalue=0):
        output.append('%02x'%(x^y))
    return bytes.fromhex(''.join(reversed(output)))
