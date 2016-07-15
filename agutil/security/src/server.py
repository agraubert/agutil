from .securesocket import SecureSocket
from ... import io
import threading
import random

random.seed()

class SecureServer:
    def __init__(self, address, port, password=None, rsabits=4096, verbose=False, timeout=3):
        if address == '' or address == 'listen':
            ss = io.SocketServer(port, queue=0)
            self.sock = SecureSocket(ss.accept(), password, rsabits, verbose, timeout)
            ss.close()
        elif not isinstance(address, io.Socket):
            self.sock = SecureSocket(io.Socket(address, port), password, rsabits, verbose, timeout)
        else:
            self.sock = SecureSocket(address, password, rsabits, verbose, timeout)
        self.tasks = {}

    def _reserve_task(self, prefix):
        taskname = prefix+"_"+"".join(str(random.randint(0,9)) for _ in range(3))
        while taskname in self.tasks:
            taskname = prefix+"_"+"".join(str(random.randint(0,9)) for _ in range(3))
        return taskname
