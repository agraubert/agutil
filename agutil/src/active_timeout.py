from contextlib import contextmanager
from socket import timeout as sockTimeout
import time


class TimeoutExceeded(sockTimeout):
    pass


class ActiveTimeout(object):
    def __init__(self, t):
        self.remainder = t
        self.original = t

    def __enter__(self):
        self.reset()
        return self

    def update(self):
        current = time.monotonic()
        if self.remainder is not None:
            self.remainder -= (current - self.last)
        self.last = current
        if self.remainder is not None and self.remainder <= 0:
            raise TimeoutExceeded("Timeout exceeded")

    def __exit__(self, *args):
        current = time.monotonic()
        if self.remainder is not None:
            self.remainder -= (current - self.last)
        self.last = current

    @property
    def thread_timeout(self):
        self.update()
        return self.remainder if self.remainder is not None else -1

    @property
    def socket_timeout(self):
        self.update()
        return self.remainder

    def reset(self):
        self.remainder = self.original
        self.last = time.monotonic()
