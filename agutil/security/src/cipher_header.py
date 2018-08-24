from ... import search_range, bytesToInt, intToBytes


class CipherHeader(object):
    _data = b'\x00'*14 + b'\xae'

    def __init__(self, header=None):
        if header is not None:
            self._data = header

    def _update(self, index, value):
        self._data = (
            self._data[:index] + value + self._data[index+len(value):]
        )[:15]

    @property
    def valid(self):
        return (
            len(self._data) == 15
            and self._data[0] == 0  # constant
            and self._data[12] == 0  # reserved block
            and self._data[13] == 0  # reserved block
            and self._data[14] == 174  # constant
            and not self.legacy_bitmask[0]  # constant
            and not self.control_bitmask[0]  # constant
            and self.legacy_bitmask[1] == self.legacy_bitmask[7]  # match
            and self.control_bitmask[1] == self.control_bitmask[7]  # match
        )

    @property
    def weight(self):
        return hamming(self._data)

    @property
    def data(self):
        return self._data + intToBytes(self.weight)

    @property
    def legacy_bitmask(self):
        return Bitmask(self._data[1])

    @legacy_bitmask.setter
    def legacy_bitmask(self, mask):
        self._update(1, intToBytes(mask.mask.data))

    @property
    def control_bitmask(self):
        return Bitmask(self._data[2])

    @control_bitmask.setter
    def control_bitmask(self, mask):
        self._update(2, intToBytes(mask.mask.data))

    @property
    def exdata_size(self):
        return self._data[3]

    @exdata_size.setter
    def exdata_size(self, size):
        self._update(3, intToBytes(size))

    @property
    def cipher_id(self):
        return self._data[4]

    @cipher_id.setter
    def cipher_id(self, num):
        self._update(4, intToBytes(num))

    @property
    def secondary_id(self):
        return self._data[5]

    @secondary_id.setter
    def secondary_id(self, num):
        self._update(5, intToBytes(num))

    @property
    def cipher_data(self):
        return self._data[6:12]

    @cipher_data.setter
    def cipher_data(self, data):
        if len(data) != 6:
            raise ValueError("cipher_data must equal 6 bytes")
        self._update(6, data)

    @property
    def use_modern_cipher(self):
        return self.control_bitmask[1]


class Bitmask(object):
    def __init__(self, n=0, values=None):
        self.mask = search_range(0, 8, False)
        if n != 0:
            self.mask.data = n
        if values is not None and not len(values) % 8:
            for i, v in enumerate(values):
                if v:
                    self.mask.add_range(i, i+1)
                else:
                    self.mask.remove_range(i, i+1)

    def __getitem__(self, i):
        return self.mask.check(i)

    def __setitem__(self, i, v):
        if v:
            self.mask.add_range(i, i+1)
        else:
            self.mask.remove_range(i, i+1)

    def set_range(self, start, stop, value=True):
        if value:
            self.mask.add_range(start, stop)
        else:
            self.mask.remove_range(start, stop)


def hamming(data):
    return sum(data) % 256
