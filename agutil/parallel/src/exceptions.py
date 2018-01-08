class _ParallelBackgroundException(Exception):
    def __init__(self, exc):
        self.exc = exc
