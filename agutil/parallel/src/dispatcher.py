from .exceptions import _ParallelBackgroundException
from .worker import ThreadWorker, ProcessWorker
from itertools import zip_longest

WORKERTYPE_THREAD = 0
WORKERTYPE_PROCESS = 1


class IterDispatcher:
    def __init__(
        self,
        func,
        *args,
        maximum=15,
        workertype=WORKERTYPE_THREAD,
        **kwargs
    ):
        self.func = func
        self.maximum = maximum
        self.args = [iter(arg) for arg in args]
        self.kwargs = {key: iter(v) for (key, v) in kwargs.items()}
        self.worker = (
            ThreadWorker if workertype == WORKERTYPE_THREAD
            else ProcessWorker
        )

    def run(self):
        self.worker = self.worker(self.maximum)
        try:
            output = []
            for args, kwargs in self._iterargs():
                # _args = args if args is not None else []
                # _kwargs = kwargs if kwargs is not None else {}
                output.append(self.worker.dispatch(
                    self.func,
                    *args,
                    **kwargs
                ))
            for callback in output:
                result = callback()
                if isinstance(result, _ParallelBackgroundException):
                    raise result.exc
                yield result
        finally:
            self.worker.close()

    def _iterargs(self):
        while True:
            args = []
            had_arg = False
            for src in self.args:
                try:
                    args.append(next(src))
                    had_arg = True
                except StopIteration:
                    return  # args.append(None)
            kwargs = {}
            for key, src in self.kwargs.items():
                try:
                    kwargs[key] = next(src)
                    had_arg = True
                except StopIteration:
                    return  # kwargs[key] = None
            if not had_arg:
                return
            yield args, kwargs

    def __iter__(self):
        yield from self.run()

    def is_alive(self):
        return self.worker.is_alive()


class DemandDispatcher:
    def __init__(self, func, maximum=15, workertype=WORKERTYPE_THREAD):
        self.maximum = maximum
        self.func = func
        self.worker = (
            ThreadWorker(self.maximum) if workertype == WORKERTYPE_THREAD
            else ProcessWorker(self.maximum)
        )

    def dispatch(self, *args, **kwargs):
        try:
            return self.worker.dispatch(self.func, *args, **kwargs)
        except BaseException:
            self.worker.close()
            raise

    def close(self):
        self.worker.close()
