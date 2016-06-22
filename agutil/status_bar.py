import sys
from shutil import get_terminal_size


class status_bar:
    def __init__(self, maximum, show_percent = False, init=True,  cols=int(get_terminal_size()[0]/2)):
        self.current = 0
        self.maximum = maximum
        self.show_percent = show_percent
        self.display = ""
        self.cols = cols
        self.cursor = 0
        self.threshold = self.maximum / self.cols
        if init:
            self._initialize()
        else:
            self.initialized = False

    def _initialize(self):
        self.initialized = True
        self._write('[%s]' % (" "*self.cols))
        if self.show_percent:
            self._write(" %0.3f%%" % ((100.0 *self.current)/(self.cols * self.threshold)))
        self._backtrack_to(1)


    def _write(self, text):
        sys.stdout.write(text)
        sys.stdout.flush()
        self.display=self.display[:self.cursor]+text+self.display[self.cursor+len(text):]
        self.cursor+=len(text)

    def _backtrack_to(self, index):
        sys.stdout.write('\b'*(self.cursor-index))
        self.cursor=index

    def update(self, value):
        if not self.initialized:
            self._initialize
        self.current = value
        self._backtrack_to(1)
        self._write('=' * int(self.current/self.threshold))
        if self.show_percent:
            self._write(" " * (self.cols - self.cursor + 1))
            self._write("] %0.3f%%" % ((100.0 *self.current)/(self.cols * self.threshold)))

    def clear(self, erase=False):
        index = self.cursor
        self._backtrack_to(0)
        if erase:
            self._write(' '*index)
            self._backtrack_to(0)


def simple_test(num):
    import time
    q = status_bar(num, True)
    for i in range(num):
        time.sleep(1)
        q.update(i)
    q.update(num)
    print()
