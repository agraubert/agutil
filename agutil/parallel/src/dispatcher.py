import threading


class _ParallelBackgroundException(Exception):
    def __init__(self, exc):
        self.exc = exc


class Dispatcher:
    def __init__(self, func, *args, maximum=15, **kwargs):
        self.func = func
        self.maximum = maximum
        self.args = [iter(arg) for arg in args]
        self.kwargs = {key: iter(v) for (key, v) in kwargs.items()}
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
                        target=Dispatcher._dispatcher,
                        args=(self,),
                        daemon=True,
                        name="Dispatcher Background Thread"
                    )
                    self.dispatcher.start()
            i = 0
            while self.isAlive() or i < len(self.output_cache):
                if i in self.output_cache:
                    self.outputEvent.clear()
                    x = self.output_cache[i]
                    if isinstance(x, _ParallelBackgroundException):
                        raise x.exc
                    yield x
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
            kwargs = {
                key: next(source) for (key, source) in self.kwargs.items()
                } if len(self.kwargs) else None
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
                self.output_cache[_parallel_id] = (
                    _ParallelBackgroundException(e)
                )
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
                            args=(i,) if args is None else [i]+[
                                arg for arg in args
                            ],
                            kwargs=kwargs if kwargs is not None else {},
                            daemon=True
                        )
                    )
                    self.threads[-1].start()
                    i += 1
                (args, kwargs) = self._extract_args()
            else:
                self.finishedEvent.wait()
                self.finishedEvent.clear()
