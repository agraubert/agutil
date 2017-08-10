import unittest
import os
from py_compile import compile
import sys
import random
import threading
import warnings
import os
import port_for as pf
startup_lock = threading.Lock()

TRAVIS = 'CI' in os.environ

def make_random_string():
    return "".join(chr(random.randint(0,255)) for i in range(25))

def server_comms(ss, payload):
    global startup_lock
    startup_lock.release()
    try:
        sock = ss.accept()
        payload.exception = False
    except ValueError:
        payload.exception = True
    sock = ss.accept()
    payload.intake=[]
    payload.output=[]
    for trial in range(5):
        payload.intake.append(sock.recv(True))
        payload.output.append(make_random_string())
        sock.send(payload.output[-1])
    sock.close()

def client_comms(_sockClass, port, payload):
    global startup_lock
    startup_lock.acquire()
    startup_lock.release()
    try:
        sock = _sockClass('localhost', port, _useIdentifier='<potato>')
        payload.exception = False
    except ValueError:
        payload.exception = True
    sock = _sockClass('localhost', port)
    payload.intake=[]
    payload.output=[]
    for trial in range(5):
        payload.output.append(make_random_string())
        sock.send(payload.output[-1])
        payload.intake.append(sock.recv(True))
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
            "socket.py"
        )
        sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(cls.script_path))))
        random.seed()

    def test_compilation(self):
        compiled_path = compile(self.script_path)
        self.assertTrue(compiled_path)

    def test_server_bind_and_communication(self):
        # warnings.simplefilter('error', ResourceWarning)
        from agutil.io import SocketServer
        from agutil.io import Socket
        ss = None
        warnings.simplefilter('ignore', ResourceWarning)
        for attempt in range(10):
            try:
                ss = SocketServer(pf.select_random())
            except OSError:
                if ss!=None:
                    ss.close()
            if ss!=None:
                break
        warnings.resetwarnings()
        self.assertIsInstance(ss, SocketServer, "Failed to bind to any ports after 10 attempts")
        startup_lock.acquire()
        server_payload = lambda x:None
        client_payload = lambda x:None
        server_thread = threading.Thread(target=server_comms, args=(ss, server_payload), daemon=True)
        client_thread = threading.Thread(target=client_comms, args=(Socket, ss.port, client_payload), daemon=True)
        server_thread.start()
        client_thread.start()
        extra = 30 if TRAVIS else 0
        if sys.version_info==(3,3):
            extra+=5
        server_thread.join(10+extra)
        self.assertFalse(server_thread.is_alive(), "Server thread still running")
        client_thread.join(10+extra)
        self.assertFalse(client_thread.is_alive(), "Client thread still running")
        ss.close()
        self.assertTrue(server_payload.exception)
        self.assertTrue(client_payload.exception)
        self.assertRaises(TypeError, client_payload.sock.send, 13)
        client_payload.sock.close()
        self.assertEqual(len(server_payload.intake), len(client_payload.output))
        self.assertEqual(len(server_payload.output), len(client_payload.intake))
        self.assertListEqual(server_payload.intake, client_payload.output)
        self.assertListEqual(server_payload.output, client_payload.intake)
