import sys
from shutil import get_terminal_size


class status_bar:
    def __init__(self, maximum, show_percent = False, init=True,  cols=int(get_terminal_size()[0]/2), update_threshold=.05):
        self.current = 0
        self.last_value = 0
        self.maximum = maximum
        self.show_percent = show_percent
        self.display = ""
        self.cols = cols
        self.cursor = 0
        self.threshold = self.maximum / self.cols
        self.update_threshold = self.threshold*update_threshold if show_percent else -1
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
        if self.cursor != 1+int(self.current/self.threshold):
            self._backtrack_to(1)
            self._write('=' * int(self.current/self.threshold))
        if self.show_percent and value>=self.last_value+self.update_threshold:
            self._write(" " * (self.cols - self.cursor + 1))
            self._write("] %0.3f%%" % ((100.0 *self.current)/(self.cols * self.threshold)))
            self.last_value = value

    def clear(self, erase=False):
        self._backtrack_to(0)
        if erase:
            self._write(' '*(self.cols + 2))
            if self.show_percent:
                self._write(' '*8)
            self._backtrack_to(0)
