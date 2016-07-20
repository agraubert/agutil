import unittest
import os
from py_compile import compile
import sys
import random
import threading
import warnings
import os
startup_lock = threading.Lock()

TRAVIS = 'CI' in os.environ
CHANNELS = ['test', 'test', 'fish', 'cat', 'test']

def make_random_string():
    return "".join(chr(random.randint(48,122)) for i in range(25))

def server_comms(queueclass, ss, payload):
    global startup_lock
    startup_lock.release()
    sock = queueclass(ss.accept())
    ss.close()
    payload.intake=[]
    payload.output=[]
    raw_output = {'test':[], 'fish':[], 'cat':[]}
    local_channels = sorted(CHANNELS, key=lambda x:random.random())
    for trial in range(5):
        raw_output[local_channels[trial]].append(make_random_string())
        sock.send(raw_output[local_channels[trial]][-1], local_channels[trial])
    for trial in range(5):
        payload.intake.append(sock.recv(CHANNELS[trial], True))
    payload.output= raw_output['test'][:2]+raw_output['fish']+raw_output['cat']+[raw_output['test'][-1]]
    payload.sock = sock

def client_comms(queueclass, _sockClass, port, payload):
    global startup_lock
    startup_lock.acquire()
    startup_lock.release()
    sock = queueclass(_sockClass('localhost', port))
    payload.intake=[]
    payload.output=[]
    raw_output = {'test':[], 'fish':[], 'cat':[]}
    local_channels = sorted(CHANNELS, key=lambda x:random.random())
    for trial in range(5):
        raw_output[local_channels[trial]].append(make_random_string())
        sock.send(raw_output[local_channels[trial]][-1], local_channels[trial])
    for trial in range(5):
        payload.intake.append(sock.recv(CHANNELS[trial], True))
    payload.output= raw_output['test'][:2]+raw_output['fish']+raw_output['cat']+[raw_output['test'][-1]]
    payload.sock = sock

class test(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.script_path = os.path.join(
            os.path.dirname(
                os.path.dirname(
                    os.path.abspath(__file__)
                )
            ),
            "agutil",
            "io",
            "src",
            "queuedsocket.py"
        )
        sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(cls.script_path))))
        random.seed()

    def test_compilation(self):
        compiled_path = compile(self.script_path)
        self.assertTrue(compiled_path)

    def test_server_bind_and_communication(self):
        # warnings.simplefilter('error', ResourceWarning)
        from agutil.io import SocketServer
        from agutil.io import QueuedSocket
        from agutil.io import Socket
        ss = None
        warnings.simplefilter('ignore', ResourceWarning)
        for port in range(4000, 5000):
            try:
                ss = SocketServer(port)
            except OSError:
                if ss!=None:
                    ss.close()
            if ss!=None:
                break
        warnings.resetwarnings()
        self.assertIsInstance(ss, SocketServer, "Failed to bind to any ports on [4000, 5000]")
        startup_lock.acquire()
        server_payload = lambda x:None
        client_payload = lambda x:None
        server_thread = threading.Thread(target=server_comms, args=(QueuedSocket, ss, server_payload), daemon=True)
        client_thread = threading.Thread(target=client_comms, args=(QueuedSocket, Socket, ss.port, client_payload), daemon=True)
        server_thread.start()
        client_thread.start()
        extra = 30 if TRAVIS else 0
        server_thread.join(10+extra)
        self.assertFalse(server_thread.is_alive(), "Server thread still running")
        client_thread.join(10+extra)
        self.assertFalse(client_thread.is_alive(), "Client thread still running")
        server_payload.sock.close()
        client_payload.sock.close()
        self.assertEqual(len(server_payload.intake), len(client_payload.output))
        self.assertEqual(len(server_payload.output), len(client_payload.intake))
        self.assertListEqual(server_payload.intake, client_payload.output)
        self.assertListEqual(server_payload.output, client_payload.intake)
