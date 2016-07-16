from .securesocket import SecureSocket
from ... import io
from . import protocols
from socket import timeout as socketTimeout
import threading
import random

random.seed()
_COMMANDS = ['kill', 'ti', 'to', 'fri', 'fro', 'fti', 'fto']
#commands: {command code byte}{hex payload size}{BAR |}{payload bytes}
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
        self.tasks = {} #Queue of taskname : thread pairs for currently running tasks
        self.authqueue = [] #Queue of task commands pending authorization
        self.schedulinglock = threading.Condition()
        self.intakelock = threading.Condition()
        self.queuedmessages = [] #Queue of decrypted received text messages
        self.schedulingqueue = [] #Queue of task commands to be scheduled
        self._shutdown = False

        #Pops new commands out of the scheduling queue, and spawns a new thread to deal with each task
        #Commands which require pre-authorization to start (ie: file transfer) are put in a holding queue instead of being scheduled
        #Once the user authorizes the command (ie: .savefile()) the task is scheduled properly
        self._scheduler = threading.Thread(target=SecureServer._scheduler_worker, args=(self,), name="SecureSocket Task Scheduling", daemon=True)
        self._scheduler.start()

        #Constantly receives from __cmd__ and adds new tasks to the scheduling queue
        self._listener = threading.Thread(target=SecureServer._listener_worker, args=(self,), name="SecureSocket Remote Task Listener", daemon=True)
        self._listener.start()

    def _reserve_task(self, prefix):
        taskname = prefix+"_"+"".join(str(random.randint(0,9)) for _ in range(3))
        while taskname in self.tasks:
            taskname = prefix+"_"+"".join(str(random.randint(0,9)) for _ in range(3))
        return taskname

    def _scheduler_worker(self):
        while not self._shutdown:
            self.schedulinglock.acquire()
            size = self.schedulinglock.wait_for(lambda :len(self.schedulingqueue), .05)
            if size:
                command = self.schedulingqueue.pop(0)
                if _COMMANDS[command[0]]=='kill':
                    self.tasks[command[1]].join(.05)
                    del self.tasks[command[1]]
                elif command[0] < len(_COMMANDS):
                    if command[0] % 2:
                        name = command[1]
                    else:
                        name = self._reserve_task(_COMMANDS[command[0]])
                    worker = protocols._assign_task(_COMMANDS[command[0]])
                    self.tasks[name] = threading.Thread(target=worker, args=(self,), name=name, daemon=True)
                    self.tasks[name].start()
            self.schedulinglock.release()

    def _listener_worker(self):
        while not self._shutdown:
            try:
                # self.sock.recvRAW('__cmd__', timeout=.1)
                cmd = self.sock.recvAES('__cmd__', True, timeout=.1)
                self.schedulinglock.acquire()
                self.schedulingqueue.append(protocols.parsecmd(cmd))
                self.schedulinglock.notify_all()
                self.schedulinglock.release()
            except socketTimeout:
                pass

    def shutdown(self, timeout=3):
        if self._shutdown:
            return
        self.schedulinglock.acquire()
        self._shutdown = True
        self.schedulinglock.release()
        self._listener.join(timeout)
        self._scheduler.join(timeout)
        self.sock.close(timeout)

    def send(self, msg, retries=1):
        self.scheduleinglock.acquire()
        self.schedulingqueue.append([
            _TEXT_PAYLOAD,
            msg,
            retries
        ])
