import unittest
import os
from py_compile import compile
import sys
import random
import threading
import warnings
startup_lock = threading.Lock()

def make_random_string():
    return "".join(chr(random.randint(0,255)) for i in range(25))

def server_comms(ss, payload):
    global startup_lock
    startup_lock.release()
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
    sock = _sockClass('localhost', port)
    payload.intake=[]
    payload.output=[]
    for trial in range(5):
        payload.output.append(make_random_string())
        sock.send(payload.output[-1])
        payload.intake.append(sock.recv(True))
    sock.close()

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
        for port in range(4000, 10000):
            try:
                ss = SocketServer(port)
            except OSError:
                if ss!=None:
                    ss.close()
            if ss!=None:
                break
        warnings.resetwarnings()
        self.assertIsInstance(ss, SocketServer)
        startup_lock.acquire()
        server_payload = lambda x:None
        client_payload = lambda x:None
        server_thread = threading.Thread(target=server_comms, args=(ss, server_payload))
        client_thread = threading.Thread(target=client_comms, args=(Socket, ss.port, client_payload))
        server_thread.start()
        client_thread.start()
        server_thread.join(10)
        self.assertFalse(server_thread.is_alive())
        client_thread.join(10)
        self.assertFalse(client_thread.is_alive())
        ss.close()
        self.assertEqual(len(server_payload.intake), len(client_payload.output))
        self.assertEqual(len(server_payload.output), len(client_payload.intake))
        self.assertListEqual(server_payload.intake, client_payload.output)
        self.assertListEqual(server_payload.output, client_payload.intake)
