from .exceptions import _ParallelBackgroundException
import threading
import multiprocessing as mp


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

        self.input_event.set()
        return unpack

    def close(self):
        self.shutdown = True

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


class ProcessWorker:
    def __init__(self, maximum):
        self.pool = mp.Pool(maximum)
        self.closed = False

    def dispatch(self, func, *args, **kwargs):
        callback = self.pool.apply_async(func, args, kwargs)
        return lambda x=None: callback.get(x)

    def close(self):
        self.pool.close()
        self.pool.join()
        self.closed = True

    def __del__(self):
        if not self.closed:
            self.pool.terminate()

    def is_alive(self):
        return not self.closed
