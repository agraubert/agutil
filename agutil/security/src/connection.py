from .securesocket import SecureSocket
from ... import io, Logger, DummyLog
from . import protocols
from socket import timeout as socketTimeout
import threading
import random
import os

random.seed()

_SECURECONNECTION_IDENTIFIER_ = '<agutil.security.secureconnection:1.0.0>'

class SecureConnection:
    def __init__(self, address, port, password=None, rsabits=4096, timeout=3, logmethod=DummyLog, _skipIdentifier=False, _useIdentifier=_SECURECONNECTION_IDENTIFIER_):
        if isinstance(logmethod, Logger):
            self.log = logmethod.bindToSender("SecureConnection")
        else:
            self.log=logmethod
        if address == '' or address == 'listen':
            ss = io.SocketServer(port, queue=0)
            self.sock = SecureSocket(ss.accept(), password, rsabits, timeout, self.log.bindToSender(self.log.name+"->SecureSocket"))
            ss.close()
        elif not isinstance(address, io.Socket):
            self.sock = SecureSocket(io.Socket(address, port), password, rsabits, timeout, self.log.bindToSender(self.log.name+"->SecureSocket"))
        else:
            self.sock = SecureSocket(address, password, rsabits, timeout, self.log.bindToSender(self.log.name+"->SecureSocket"))
        self.log("SecureConnection now initialized.  Starting background threads...")
        self.address = address
        self.port = port
        self.tasks = {} #Queue of taskname : thread pairs for currently running tasks
        self.authqueue = [] #Queue of task commands pending authorization
        self.filemap = {} #mapping of auth_key : filename pairs for files ready to transfer
        self.pending_tasks = threading.Event()
        self.intakeEvent = threading.Event()
        self.pendingRequest = threading.Event()
        self.transferComplete = threading.Event()
        self.killedtask = threading.Event()
        self.completed_transfers = set()
        self.queuedmessages = [] #Queue of decrypted received text messages
        self.schedulingqueue = [] #Queue of task commands to be scheduled
        self._shutdown = False
        self._init_shutdown = False

        #Pops new commands out of the scheduling queue, and spawns a new thread to deal with each task
        #Commands which require pre-authorization to start (ie: file transfer) are put in a holding queue instead of being scheduled
        #Once the user authorizes the command (ie: .savefile()) the task is scheduled properly
        self._scheduler = threading.Thread(target=SecureConnection._scheduler_worker, args=(self,), name="SecureConnection Task Scheduling", daemon=True)
        self._scheduler.start()

        #Constantly receives from __cmd__ and adds new tasks to the scheduling queue
        self._listener = threading.Thread(target=SecureConnection._listener_worker, args=(self,), name="SecureConnection Remote Task Listener", daemon=True)
        self._listener.start()

        if not _skipIdentifier:
            self.sock.sendRAW(_useIdentifier, '__protocol__')
            remoteID = self.sock.recvRAW('__protocol__', True)
            if remoteID != _useIdentifier:
                self.log("The remote socket provided an invalid SecureConnection protocol identifier. (Theirs: %s) (Ours: %s)" % (
                    remoteID,
                    _useIdentifier
                ), "WARN")
                self.close(_remote=True)
                raise ValueError("The remote socket provided an invalid identifier at the SecureConnection level")

    def _reserve_task(self, prefix):
        taskname = prefix+"_"+"".join(str(random.randint(0,9)) for _ in range(3))
        while taskname in self.tasks:
            taskname = prefix+"_"+"".join(str(random.randint(0,9)) for _ in range(3))
        return taskname

    def _scheduler_worker(self):
        self.log("SecureConnection Task Scheduling thread active")
        while not self._shutdown:
            if len(self.schedulingqueue):
                self.pending_tasks.clear()
                command = self.schedulingqueue.pop(0)
                self.log("Scheduling new command: %d"%command['cmd'], "DETAIL")
                if protocols._COMMANDS[command['cmd']]=='kill':
                    self.tasks[command['name']].join(.05)
                    del self.tasks[command['name']]
                    if self._init_shutdown and not len(self.tasks):
                        self.killedtask.set()
                elif command['cmd'] < len(protocols._COMMANDS):
                    if command['cmd'] % 2:
                        name = command['name']
                    else:
                        name = self._reserve_task(protocols._COMMANDS[command['cmd']])
                    worker = protocols._assign_task(protocols._COMMANDS[command['cmd']])
                    self.tasks[name] = threading.Thread(target=worker, args=(self,command,name), name=name, daemon=True)
                    self.tasks[name].start()
                    self.log("Started new task '%s'"%name, "DEBUG")
            else:
                self.pending_tasks.wait(.05)
        self.log("SecureConnection Task Scheduling thread inactive")

    def _listener_worker(self):
        self.log("SecureConnection Remote Command thread active")
        while not self._init_shutdown:
            try:
                # self.sock.recvRAW('__cmd__', timeout=.1)
                cmd = self.sock.recvAES('__cmd__', timeout=.1, _logInit=False)
                self.log("Remote command received", "DETAIL")
                self.schedulingqueue.append(protocols.unpackcmd(cmd))
                self.pending_tasks.set()
            except socketTimeout:
                pass
        self.log("SecureConnection Remote Command thread inactive")

    def send(self, msg, retries=1):
        if self._init_shutdown:
            self.log("Attempt to use the SecureConnection after shutdown", "WARN")
            raise IOError("This SecureConnection has already initiated shutdown")
        if type(msg)==str:
            msg=msg.encode()
        elif type(msg)!=bytes:
            self.log("Attempt to send message which was not str or bytes", "WARN")
            raise TypeError("msg argument must be str or bytes")
        self.log("Outgoing text message scheduled", "DEBUG")
        self.schedulingqueue.append({
            'cmd': protocols.lookupcmd('to'),
            'msg': msg,
            'retries': retries
        })
        self.pending_tasks.set()

    def read(self, decode=True, timeout=-1):
        if self._init_shutdown:
            self.log("Attempt to use the SecureConnection after shutdown", "WARN")
            raise IOError("This SecureConnection has already initiated shutdown")
        if timeout == -1:
            timeout = self.sock.timeout
        self.log("Waiting to receive incoming text message", "DEBUG")
        self.intakeEvent.wait(timeout)
        if not len(self.queuedmessages):
            raise socketTimeout("No message recieved within the specified timeout")
        msg = self.queuedmessages.pop(0)
        self.intakeEvent.clear()
        if decode:
            msg = msg.decode()
        return msg

    def sendfile(self, filename):
        if self._init_shutdown:
            self.log("Attempt to use the SecureConnection after shutdown", "WARN")
            raise IOError("This SecureConnection has already initiated shutdown")
        if not os.path.isfile(filename):
            self.log("Unable to determine file specified by path '%s'"%filename, "ERROR")
            raise FileNotFoundError("The provided filename does not exist or is invalid")
        self.log("Outgoing file request scheduled", "DEBUG")
        self.schedulingqueue.append({
            'cmd': protocols.lookupcmd('fro'),
            'filepath': os.path.abspath(filename)
        })
        self.pending_tasks.set()

    def savefile(self, destination, timeout=-1, force=False):
        if self._init_shutdown:
            self.log("Attempt to use the SecureConnection after shutdown", "WARN")
            raise IOError("This SecureConnection has already initiated shutdown")
        if timeout == -1:
            timeout = self.sock.timeout
        self.log("Waiting to receive incoming file request", "DEBUG")
        while not len(self.authqueue):
            result = self.pendingRequest.wait(timeout)
            if not result:
                raise SocketTimeout("No file transfer requests recieved within the specified timeout")
            self.pendingRequest.clear()
        (filename, auth) = self.authqueue.pop(0)
        if not force:
            print("The remote socket is attempting to send the file '%s'")
            accepted = False
            choice = ""
            while not accepted:
                choice = input("Accept this transfer (y/n): ")
                choice = choice.lower()
                if choice not in {'y', 'n', 'yes', 'no'}:
                    print("Please enter y, Y, yes, n, N, or no")
                else:
                    accepted = True
            if choice[0] != 'y':
                self.log("User rejected transfer of file '%s'"%filename)
                self.schedulingqueue.append({
                    'cmd': protocols.lookupcmd('fti'),
                    'auth': auth,
                    'reject': True
                })
                self.pending_tasks.set()
                return
        self.log("Accepted transfer of file '%s'"%filename)
        self.schedulingqueue.append({
            'cmd': protocols.lookupcmd('fti'),
            'auth': auth,
            'filepath': destination
        })
        self.pending_tasks.set()
        self.log("Waiting for transfer to complete...", "DEBUG")
        while destination not in self.completed_transfers:
            result = self.transferComplete.wait(timeout)
            if not result:
                raise SocketTimeout("File transfer did not complete in the specified timeout")
            self.transferComplete.clear()
        self.completed_transfers.remove(destination)
        self.log("File transfer complete", "DEBUG")
        return destination

    def shutdown(self, timeout=-1):
        self.close(timeout)

    def close(self, timeout=-1, _remote=False):
        if self._shutdown or self._init_shutdown:
            return
        if timeout == -1:
            timeout = self.sock.timeout
        self._init_shutdown = True
        self.log("Initiating "+("remote " if _remote else "")+"shutdown of SecureConnection")
        self._listener.join(.2)
        self.killedtask.wait(timeout)
        self._shutdown = True
        self._scheduler.join(.1)
        if not _remote:
            self.sock.sendAES(protocols.packcmd('dci'), '__cmd__')
        self.sock.close()
        self.log.close()
