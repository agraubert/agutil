import sys
from shutil import get_terminal_size


class status_bar:
    def __init__(self, maximum, show_percent = False, init=True,  prepend="", append="", cols=int(get_terminal_size()[0]/2), update_threshold=.00005, debugging=False, transcript=None):
        if maximum <=0:
            raise ValueError("status_bar maximum must be >0 (maximum was {val})".format(
                val=repr(maximum)
            ))
        self.current = 0
        self.logger = None if not transcript else open(transcript, mode='w')
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
        self.update_threshold = self.maximum*update_threshold if show_percent else -1
        self.progress = 0
        self.pending_text_update=False
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
            self._write(" %0.3f%%" % ((100.0 *self.current)/(self.cols * self.threshold)))
        if len(self.post):
            self.post_start = self.cursor+1
            self._write(self.post)
        self._backtrack_to(1+len(self.pre))
        self.pending_text_update=False


    def _write(self, text):
        if not self.debugging:
            sys.stdout.write(text)
            sys.stdout.flush()
        self.display=self.display[:self.cursor]+text+self.display[self.cursor+len(text):]
        self.cursor+=len(text)
        if self.logger:
            self._log("\n"+("-"*8)+"\nWRITE TEXT: \""+text+"\"\n")
            self._log("Cursor: "+str(self.cursor)+" VALUE: "+str(self.current)+" PROGRESS: "+str(self.progress)+"\n")
            if len(self.pre):
                self._log("PREPENDED TEXT:"+self.pre+"\n")
            if len(self.post):
                self._log("APPENDED TEXT:"+self.post+"\n")
            self._log((" "*(self.cursor-1)+"V\n"))
            self._log(self.display)
            self.logger.flush()

    def _backtrack_to(self, index):
        if index < self.cursor:
            if not self.debugging:
                sys.stdout.write('\b'*(self.cursor-index))
            self.cursor=index
            if self.logger:
                self._log("\n"+("-"*8)+"\nCURSOR BACKTRACK TO: "+str(index)+"\n")
                self._log((" "*(self.cursor-1)+"V\n"))
                self._log(self.display)
                self.logger.flush()

    def _log(self, text):
        if self.logger:
            self.logger.write(text)

    def update(self, value):
        if self.pending_text_update or not self.initialized:
            self._initialize()
        if value < 0:
            value = 0
        elif value > self.maximum:
            value = self.maximum
        self.current = value
        if self.progress != int(self.current/self.threshold):
            self._backtrack_to(1+len(self.pre))
            self._write('=' * int(self.current/self.threshold))
            if int(self.current/self.threshold) < self.progress:
                self._write(" " * (self.cols - (self.cursor-len(self.pre)) + 1))
            self.progress = int(self.current/self.threshold)
        if self.show_percent and abs(value-self.last_value)>=self.update_threshold:
            if self.cursor <= self.cols+1+len(self.pre):
                self._write(" " * (self.cols - (self.cursor-len(self.pre)) + 1))
            else:
                self._backtrack_to(1+self.cols+len(self.pre))
            self._write("] %0.3f%%" % ((100.0 *self.current)/(self.cols * self.threshold)))
            if self.cursor >= self.post_start:
                self.post_start = self.cursor +1
                self._write(self.post)
            self.last_value = value

    def clear(self, erase=False):
        self._backtrack_to(0)
        if erase:
            self._write(' '*(self.cols + 2+len(self.pre)))
            if self.show_percent:
                self._write(' '*9)
            self._write(' '*(len(self.post)))
            self._backtrack_to(0)
        if self.logger:
            self.logger.close()

    def prepend(self, text, updateText=True):
        self.pre = text
        if self.initialized and updateText:
            self._initialize()
            self.update(self.value)
        self.pending_text_update |= not updateText

    def append(self, text, updateText=True):
        self.post = text
        if self.initialized and updateText:
            self._initialize()
            self.update(self.value)
        self.pending_text_update |= not updateText
