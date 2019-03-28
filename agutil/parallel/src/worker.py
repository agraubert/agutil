from .exceptions import _ParallelBackgroundException
import threading
import multiprocessing as mp
from functools import wraps


def execute_with_context(ctx, func):

    @wraps(func)
    def call(*args, **kwargs):
        with ctx:
            return func(*args, **kwargs)

    return call


class ThreadWorker:
    def __init__(self, maximum):
        self.maximum = maximum
        self.workers = []
        self.output_cache = {}
        self.queue = []
        self.input_event = threading.Event()
        self.output_event = threading.Event()
        self.lock = threading.Lock()
        self.shutdown = False
        self.worker = threading.Thread(
            target=ThreadWorker._worker,
            args=(self,),
            daemon=True,
            name="ThreadWorker dispatching thread"
        )
        self.worker.start()

    def dispatch(self, func, *args, **kwargs):
        return self.work(func, *args, **kwargs)

    def work(self, func, *args, **kwargs):
        evt = threading.Event()
        with self.lock:
            key = id(evt)
            self.queue.append([func, args, kwargs, evt, key])

        def unpack():
            evt.wait()
            result = self.output_cache[key]
            if isinstance(result, _ParallelBackgroundException):
                raise result.exc
            return result

        def poll():
            return evt.is_set()

        self.input_event.set()
        unpack.func = func
        unpack.args = args
        unpack.kwargs = kwargs
        unpack.poll = poll
        return unpack

    def close(self):
        self.shutdown = True

    # def halt(self):
    #     self.close()

    def is_alive(self):
        return not self.shutdown

    def _work(self, func, args, kwargs, evt, key):
        try:
            result = func(*args, **kwargs)
            self.output_cache[key] = result
        except BaseException as e:
            self.output_cache[key] = (
                _ParallelBackgroundException(e)
            )
            # raise e
        finally:
            evt.set()
            self.output_event.set()

    def _worker(self):
        while not self.shutdown:
            if len(self.queue):
                if len(self.workers) < self.maximum:
                    with self.lock:
                        func, args, kwargs, evt, key = self.queue.pop(0)
                    self.workers.append(threading.Thread(
                        target=ThreadWorker._work,
                        args=(self, func, args, kwargs, evt, key),
                        daemon=True
                    ))
                    self.workers[-1].start()
                else:
                    if self.output_event.wait(1):
                        self.output_event.clear()
            else:
                if self.input_event.wait(1):
                    self.input_event.clear()
            with self.lock:
                self.workers = [
                    worker for worker in self.workers if worker.is_alive()
                ]


def process_runner(func, *args, **kwargs):
    try:
        return func(*args, **kwargs)
    except BaseException as e:
        return _ParallelBackgroundException(e)


class ProcessWorker:
    def __init__(self, maximum):
        self.pool = mp.Pool(maximum)
        self.closed = False

    def dispatch(self, func, *args, **kwargs):
        return self.work(func, *args, **kwargs)

    def work(self, func, *args, **kwargs):
        callback = self.pool.apply_async(
            process_runner,
            [func] + list(args),
            kwargs
        )

        def get(timeout=None):
            result = callback.get(timeout)
            if isinstance(result, _ParallelBackgroundException):
                self.halt()
                raise result.exc
            return result

        get.func = func
        get.args = args
        get.kwargs = kwargs
        get.poll = callback.ready
        return get

    def close(self):
        self.pool.close()
        self.pool.join()
        self.closed = True

    def halt(self):
        self.pool.terminate()
        self.pool.join()
        self.closed = True

    def __del__(self):
        if not self.closed:
            self.pool.terminate()

    def is_alive(self):
        return not self.closed
