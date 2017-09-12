from .dispatcher import Dispatcher, _ParallelBackgroundException
import threading


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


def parallelize(arg=15):

    def wrap(func, parallel_max=15):

        def call(*args, **kwargs):
            yield from Dispatcher(func, *args, maximum=parallel_max, **kwargs)

        return call

    if callable(arg):
        return wrap(arg)
    else:
        return lambda x: wrap(x, arg)


def parallelize2(_arg=15):
    def _par2(func, parallel_max=15):
        cache = {}
        slot = Counter()
        count = Counter()
        condition = threading.Condition()

        def wrap(n, func):
            event = threading.Event()

            def work(*args, **kwargs):
                with condition:
                    condition.wait_for(lambda: count.val < parallel_max)
                    count.incr()
                try:
                    result = func(*args, **kwargs)
                    cache[n] = result
                except BaseException as e:
                    cache[n] = _ParallelBackgroundException(e)
                finally:
                    with condition:
                        count.decr()
                        condition.notify()
                    event.set()

            return (work, event)

        def call(*args, **kwargs):
            with condition:
                n = slot.val
                slot.incr()
                (targ, evt) = wrap(n, func)
                threading.Thread(
                    target=targ,
                    args=args,
                    kwargs=kwargs,
                    daemon=True
                ).start()

            def unpack():
                evt.wait()
                x = cache[n]
                if isinstance(x, _ParallelBackgroundException):
                    raise x.exc
                return x

            return unpack

        return call

    if callable(_arg):
        return _par2(_arg)
    else:
        return lambda x: _par2(x, _arg)
