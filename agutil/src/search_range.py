class search_range:
    def __init__(self, start=0, stop=0, fill=True):
        if stop < start:
            raise ValueError("search_range stop must be >= start (start: {start}, stop: {stop})".format(
                start = start,
                stop = stop
            ))
        self.offset = start
        self.data_range = stop-start if stop>=start else 0
        self.data = 0
        self.rc = 0
        if fill and self.data_range>0:
            self.data = (1<<self.data_range)-1
            self.rc = self.data_range

    def add_range(self, start, stop):
        old = self.data
        if start < self.offset:
            self.data <<= (self.offset-start)
            old <<=(self.offset - start)
            self.data_range += self.offset-start
            self.offset = start
        if stop > self.offset+self.data_range:
            self.data_range = stop - self.offset
        if stop < start:
            return
        self.data |= ((1<<(stop-start))-1)<<(start-self.offset)
        new_bits = self.data & (~old)
        new_bits >>= (start-self.offset)
        for i in range(start,stop):
            if new_bits & 1:
                self.rc+=1
            new_bits>>=1

    def remove_range(self, start, stop):
        old = self.data
        if start < self.offset:
            start = self.offset
        if stop > self.data_range + self.offset:
            stop = self.data_range + self.offset
        if stop < start:
            return
        self.data &= ~(((1<<(stop-start))-1)<<(start-self.offset))
        new_bits = old & (~self.data)
        new_bits>>=(start-self.offset)
        for i in range(start, stop):
            if new_bits & 1:
                self.rc-=1
            new_bits>>=1

    def check(self, coord):
        if coord < self.offset or coord-self.offset > self.data_range:
            return False
        return bool(self.data & (1 << coord-self.offset))

    def check_range(self, start, stop):
        if start < self.offset:
            start = self.offset
        if start > self.offset + self.data_range:
            return False
        if stop < start:
            return False
        return bool(self.data & ((1<<(stop-start))-1)<<(start-self.offset))

    def _merge(self, other, op):
        if type(other)!=search_range:
            raise TypeError("Method not supported with operand of type "+str(type(other)))
        lower = min(self.offset, other.offset)
        size = max(self.data_range+self.offset, other.data_range+other.offset) - lower
        output = search_range(lower, size+lower, False)
        output.data = op(
            self.data<<(self.offset-lower),
            other.data<<(other.offset-lower)
        )
        output.rc = sum(1 for _ in output)
        return output

    def union(self, other):
        return self._merge(other, lambda x,y : x | y)

    def __or__(self, other):
        return self.union(other)

    def __add__(self, other):
        return self.union(other)

    def difference(self, other):
        return self._merge(other, lambda x,y : x & (~y))

    def __sub__(self, other):
        return self.difference(other)

    def intersection(self, other):
        return self._merge(other, lambda x,y: x & y)

    def __and__(self, other):
        return self.intersection(other)

    def __mul__(self, other):
        return self.intersection(other)

    def __iter__(self):
        index = 1
        for i in range(self.data_range):
            if self.data & index:
                yield self.offset + i
            index <<= 1

    def gen_ranges(self):
        active = False
        start = 0
        index = 1
        for i in range(self.data_range):
            good = self.data & index
            if active and not good:
                active = False
                yield (start, i+self.offset)
            elif good and not active:
                active = True
                start = i+self.offset
            index <<= 1
        if active:
            yield (start, self.data_range+self.offset)

    def __str__(self):
        return "search_range < "+(", ".join('['+str(item[0])+", "+str(item[1])+')' for item in self.gen_ranges()))+" >"

    def __repr__(self):
        return "["+", ".join(str(i) for i in self)+"]"

    def range_count(self):
        return self.rc

    def __bool__(self):
        return bool(self.range_count())
