import sys
from math import log10
from shutil import get_terminal_size


class status_bar:

    @classmethod
    def iter(cls, iterable, maximum=None, *_, iter_debug=False, **kwargs):
        if maximum is None:
            maximum = len(iterable)
        with status_bar(maximum, **kwargs) as bar:
            if iter_debug:
                yield bar
            for obj in iterable:
                yield obj
                bar.update()

    def __init__(
        self,
        maximum,
        show_percent=True,
        init=True,
        prepend="",
        append="",
        cols=int(get_terminal_size()[0]/2),
        update_threshold=.00005,
        debugging=False
    ):
        if maximum <= 0:
            raise ValueError(
                "status_bar maximum must be >0 (maximum was {val})".format(
                    val=repr(maximum)
                )
            )
        self.current = 0
        self.last_value = 0
        self.maximum = maximum
        self.show_percent = show_percent
        self.display = ""
        self.cols = cols
        self.pre = prepend
        self.post = append
        self.post_start = 0
        self.cursor = 0
        self.threshold = self.maximum / self.cols
        self.debugging = debugging
        self.update_threshold = (
            self.maximum*update_threshold if show_percent else -1
        )
        self.progress = 0
        self.pending_text_update = False
        if init:
            self._initialize()
        else:
            self.initialized = False

    def _initialize(self):
        self.initialized = True
        self._backtrack_to(0)
        self.progress = 0
        if len(self.pre):
            self._write(self.pre)
        self._write('[%s]' % (" "*self.cols))
        if self.show_percent:
            self._write(" %0.3f%%" % (
                (100.0 * self.current)/(self.cols * self.threshold)
            ))
        if len(self.post):
            self.post_start = self.cursor+1
            self._write(self.post)
        self._backtrack_to(1+len(self.pre))
        self.pending_text_update = False

    def _write(self, text):
        if not self.debugging:
            sys.stdout.write(text)
            sys.stdout.flush()
        self.display = (
            self.display[:self.cursor] + text +
            self.display[self.cursor + len(text):]
        )
        self.cursor += len(text)

    def _backtrack_to(self, index):
        if index < self.cursor:
            if not self.debugging:
                sys.stdout.write('\b'*(self.cursor-index))
            self.cursor = index

    def update(self, value=None):
        if self.pending_text_update or not self.initialized:
            self._initialize()
        if value is None:
            value = self.current + 1
        if value < 0:
            value = 0
        elif value > self.maximum:
            value = self.maximum
        self.current = value
        if self.progress != int(self.current/self.threshold):
            self._backtrack_to(1+len(self.pre))
            self._write('=' * int(self.current/self.threshold))
            if int(self.current/self.threshold) < self.progress:
                self._write(
                    " " * (self.cols - (self.cursor-len(self.pre)) + 1)
                )
            self.progress = int(self.current/self.threshold)
        if (
            self.show_percent and
            abs(value-self.last_value) >= self.update_threshold
        ):
            if self.cursor <= self.cols+1+len(self.pre):
                self._write(
                    " " * (self.cols - (self.cursor-len(self.pre)) + 1)
                )
            else:
                self._backtrack_to(1+self.cols+len(self.pre))
            current_percent = (
                (100.0 * self.current)/(self.cols * self.threshold)
            )
            self._write("] %0.3f%%" % (current_percent))
            last_percent = (
                (100.0 * self.last_value)/(self.cols * self.threshold)
            )
            backtrack = (
                last_percent > 0 and
                (
                    current_percent == 0 or
                    int(log10(current_percent)) < int(log10(last_percent))
                )
            )
            if self.cursor >= self.post_start or backtrack:
                self.post_start = self.cursor + 1
                self._write(self.post)
                if backtrack:
                    self._write(' ')
                    self._backtrack_to(self.cursor-1)
                    self.display = self.display[:-1]
            self.last_value = value

    def clear(self, erase=True):
        self._backtrack_to(0)
        if erase:
            self._write(' '*(self.cols + 2+len(self.pre)))
            if self.show_percent:
                self._write(' '*9)
            self._write(' '*(len(self.post)))
            self._backtrack_to(0)

    def prepend(self, text, updateText=True):
        self.pre = text
        if self.initialized and updateText:
            self._initialize()
            self.update(self.last_value)
        self.pending_text_update |= not updateText

    def append(self, text, updateText=True):
        self.post = text
        if self.initialized and updateText:
            self._initialize()
            self.update(self.last_value)
        self.pending_text_update |= not updateText

    def __enter__(self):
        self._initialize()
        return self

    def __exit__(self, type, value, traceback):
        self.clear(True)
