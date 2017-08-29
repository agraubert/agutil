import threading
import time

def parallelize(arg=15):
    def wrap(func, parallel_max=15):
        def call(*args, **kwargs):
            yield from Dispatcher(func, *args, maximum=parallel_max, **kwargs)
        return call
    if callable(arg):
        return wrap(arg)
    else:
        return lambda x: wrap(x, arg)

# given a function, and an args/kwargs iterable
# return a generator
# start a dispatching thread, when one thread returns, dispatch a new thread (up to n)
# stash return data in a cache, generator returns objects sequentially (in order their args appeared)
# waits until the next (in order of args, not return) value is ready
class Dispatcher:
    def __init__(self, func, *args, maximum=15, **kwargs):
        self.func = func
        self.maximum = maximum
        self.args = [iter(arg) for arg in args]
        self.kwargs = {key:iter(v) for (key, v) in kwargs.items()}
        self.output_cache = {}
        self.threads = []
        self.count = 0
        self.lock = threading.Lock()
        self.outputEvent = threading.Event()
        self.finishedEvent = threading.Event()
        self.shutdown = False
        self.dispatcher = None

    def run(self):
        try:
            with self.lock:
                if self.dispatcher is None:
                    self.dispatcher = threading.Thread(
                        target= Dispatcher._dispatcher,
                        args=(self,),
                        daemon=True,
                        name="Dispatcher Background Thread"
                    )
                    self.dispatcher.start()
            i = 0
            while self.isAlive() or i < len(self.output_cache):
                if i in self.output_cache:
                    self.outputEvent.clear()
                    yield self.output_cache[i]
                    i += 1
                else:
                    self.outputEvent.wait()
        finally:
            self.shutdown = True

    def __iter__(self):
        yield from self.run()

    def _extract_args(self):
        try:
            args = [next(arg) for arg in self.args] if len(self.args) else None
        except StopIteration:
            args = None
        try:
            kwargs = {key:next(source) for (key, source) in self.kwargs.items()} if len(self.kwargs) else None
        except StopIteration:
            kwargs = None
        return (args, kwargs)

    def isAlive(self):
        if self.dispatcher.isAlive():
            return True
        for i in range(len(self.threads)):
            if self.threads[i].isAlive():
                return True
        return False

    def _dispatcher(self):
        (args, kwargs) = self._extract_args()
        i = 0
        def work(_parallel_id, *args, **kwargs):
            self.lock.acquire()
            self.count += 1
            self.lock.release()
            try:
                result = self.func(*args, **kwargs)
                self.output_cache[_parallel_id] = result
            except BaseException as e:
                self.output_cache[_parallel_id] = e
                raise e
            finally:
                self.lock.acquire()
                self.count -= 1
                self.lock.release()
                self.outputEvent.set()
                self.finishedEvent.set()

        while (args is not None or kwargs is not None) and not self.shutdown:
            if self.count < self.maximum:
                with self.lock:
                    self.threads.append(
                        threading.Thread(
                            target=work,
                            args=(i,) if args is None else (i, *args),
                            kwargs=kwargs if kwargs is not None else {},
                            daemon=True
                        )
                    )
                    self.threads[-1].start()
                    i+=1
                (args, kwargs) = self._extract_args()
            else:
                self.finishedEvent.wait()
                self.finishedEvent.clear()


class counter:
    def __init__(self):
        self.val = 0

    def incr(self):
        self.val += 1

    def decr(self):
        self.val -= 1

#dispatches a thread and returns callback object
#threads wait for capacity, then executes
#must call the callback object to unpack value
def par2(*_args, **_kwargs):
    parallel_max = 15
    throttled=False
    def _par2(func):
        cache = {}
        slot = counter()
        count = counter()
        condition = threading.Condition()
        def wrap(n, func):
            event = threading.Event()
            def work(*args, **kwargs):
                with condition:
                    if not throttled:
                        condition.wait_for(lambda :count.val < parallel_max)
                        count.incr()
                try:
                    result = func(*args, **kwargs)
                    cache[n] = result
                except BaseException as e:
                    cache[n] = e
                finally:
                    with condition:
                        count.decr()
                        condition.notify()
                    event.set()
            return (work, event)
        def call(*args, **kwargs):
            with condition:
                if throttled:
                    condition.wait_for(lambda :count.val < parallel_max)
                    count.incr()
                n = slot.val
                slot.incr()
                (targ, evt) = wrap(n, func)
                threading.Thread(
                    target= targ,
                    args= args,
                    kwargs= kwargs,
                    daemon= True
                ).start()
            def unpack():
                evt.wait()
                return cache[n]
            return unpack
        return call
    if len(_args) == 1 and callable(_args[0]):
        return _par2(_args[0])
    else:
        if 'throttled' in _kwargs:
            thottled = _kwargs['throttled']
        elif len(_args) == 2:
            throttled = _args[1]
        elif len(_args) == 1 and 'maximum' in _kwargs:
            throttled = _args[1]
        if 'maximum' in _kwargs:
            parallel_max = _kwargs['maximum']
        elif len(_args) == 1:
            parallel_max = _args[0]
        return _par2


import random
@par2
def foo(n):
    time.sleep(random.random()*10)
    return n
