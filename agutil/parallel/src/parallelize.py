from .dispatcher import (
    IterDispatcher,
    DemandDispatcher,
    WORKERTYPE_THREAD,
    WORKERTYPE_PROCESS
)
from .exceptions import _ParallelBackgroundException
import threading
from functools import wraps


class Counter:
    def __init__(self):
        self.val = 0

    def incr(self, n=1):
        self.val += n

    def decr(self, n=1):
        self.val -= n

    def __int__(self):
        return self.val

    def __repr__(self):
        return '<Counter: %d>' % self.val

    def __iadd__(self, other):
        self.val += int(other)

    def __isub__(self, other):
        self.val -= int(other)


def parallelize(maximum=15, workertype=WORKERTYPE_THREAD):

    def wrap(func):

        @wraps(func)
        def call(*args, **kwargs):
            yield from IterDispatcher(
                func,
                *args,
                maximum=maximum,
                workertype=workertype,
                **kwargs
            )

        return call

    return wrap


def parallelize2(maximum=15, workertype=WORKERTYPE_THREAD):

    def wrap(func):
        dispatcher = DemandDispatcher(
            func,
            maximum=maximum,
            workertype=workertype
        )

        @wraps(func)
        def call(*args, **kwargs):
            return dispatcher.dispatch(*args, **kwargs)

        call._close_dispatcher = lambda: dispatcher.close()
        return call

    return wrap
