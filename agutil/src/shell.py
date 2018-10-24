import os
import sys
import subprocess
import threading
from shlex import quote


class ShellReturnObject:
    def __init__(self, command, stdoutAdapter, returncode):
        self.returncode = int(returncode)
        self.buffer = b''
        self.rawbuffer = stdoutAdapter.readBuffer()
        tmp = []
        for char in self.rawbuffer:
            if char == 8:  # backspace
                tmp.pop()
            else:
                tmp.append(char)
        self.buffer = b''.join(bytes.fromhex('%02x' % c) for c in tmp)
        self.command = ""+command

    def __repr__(self):
        return "<ShellReturnObject returncode=%d command=\"%s\">" % (
            self.returncode,
            self.command
        )


class StdOutAdapter:
    def __init__(self, display: bool):
        (self.readFD, self.writeFD) = os.pipe()
        self.buffer = b''
        self.display = bool(display)
        self._thread = threading.Thread(
            target=StdOutAdapter._threadWorker,
            args=(self,),
            daemon=True
        )
        self._thread.start()

    def kill(self):
        try:
            os.close(self.writeFD)
        except OSError:
            pass
        self._thread.join()
        try:
            os.close(self.readFD)
        except OSError:
            pass

    def readBuffer(self):
        if self._thread.is_alive():
            return b''
        return self.buffer

    def _threadWorker(self):
        intake = os.read(self.readFD, 64)
        while len(intake):
            if(self.display):
                os.write(sys.stdout.fileno(), intake)
            self.buffer += intake
            intake = os.read(self.readFD, 64)


def cmd(expr, display=True):
    if type(expr) in {list, tuple}:
        expr = " ".join([quote(token) for token in expr])
    adapter = StdOutAdapter(display)
    stdinFD = os.dup(sys.stdin.fileno())
    proc = subprocess.Popen(
        expr,
        shell=True,
        stdout=adapter.writeFD,
        stderr=adapter.writeFD,
        stdin=stdinFD,
        universal_newlines=False,
        executable=os.environ['SHELL'] if 'SHELL' in os.environ else None
    )
    proc.wait()
    adapter.kill()
    os.close(stdinFD)
    return ShellReturnObject(expr, adapter, proc.returncode)
