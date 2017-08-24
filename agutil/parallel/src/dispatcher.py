import threading
import time

def _func(i):
    time.sleep(i)
    return i

def parallelize(func, maximum=15):
    def call(args=None, kwargs=None):
        yield from Dispatcher(func, args, kwargs, maximum)
    return call

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
        self.kwargs = {key:iter(v) for (key, v) in kwargs}
        self.output_cache = {}
        self.threads = []
        self.count = 0
        self.lock = threading.Lock()
        self.outputEvent = threading.Event()
        self.finishedEvent = threading.Event()

    def run(self):
        self.dispatcher = threading.Thread(
            target= Dispatcher._dispatcher,
            args=(self,),
            daemon=True,
            name="Dispatcher Background Thread"
        )
        self.dispatcher.start()
        time.sleep(0.5)
        i = 0
        while self._still_running() or i < len(self.output_cache):
            if i in self.output_cache:
                self.outputEvent.clear()
                yield self.output_cache[i]
                i += 1
            else:
                self.outputEvent.wait()

    def __iter__(self):
        yield from self.run()

    def _extract_args(self):
        try:
            args = [next(arg) for arg in self.args] if len(self.args) else None
        except StopIteration:
            args = None
        try:
            kwargs = {key:next(source) for (key, source) in self.kwargs} if len(self.kwargs) else None
        except StopIteration:
            kwargs = None
        return (args, kwargs)

    def _still_running(self):
        if self.dispatcher.isAlive():
            return True
        for i in range(len(self.threads)):
            if self.threads[i].isAlive():
                return True
        return False

    def _dispatcher(self):
        (args, kwargs) = self._extract_args()
        i = 0
        def work(i, *args, **kwargs):
            self.lock.acquire()
            self.count += 1
            self.lock.release()
            try:
                result = self.func(*args, **kwargs)
                self.output_cache[i] = result
            except BaseException as e:
                self.output_cache[i] = e
            finally:
                self.lock.acquire()
                self.count -= 1
                self.lock.release()
                self.outputEvent.set()
                self.finishedEvent.set()

        while args is not None or kwargs is not None:
            if self.count < self.maximum:
                self.lock.acquire()
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
                self.lock.release()
                (args, kwargs) = self._extract_args()
            else:
                self.finishedEvent.wait()
                self.finishedEvent.clear()
