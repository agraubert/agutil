import unittest
import os
from py_compile import compile
import sys
import random
import threading
import warnings
import os

TRAVIS = 'CI' in os.environ

def make_random_string():
    return "".join(chr(random.randint(48,122)) for i in range(25))

def server_comms(secureClass, port, payload):
    sock = secureClass('listen', port, password='password', rsabits=1024)
    payload.intake=[]
    payload.output=[]
    sock.sock.sendRAW("+")
    for trial in range(5):
        payload.output.append(make_random_string())
        sock.send(payload.output[-1])
    for trial in range(5):
        payload.intake.append(sock.read())
    payload.sock = sock

def client_comms(secureclass, port, payload):
    sock = secureclass('localhost', port, password='password', rsabits=1024, verbose=False)
    payload.intake=[]
    payload.output=[]
    payload.comms_check = sock.sock.recvRAW(decode=True)
    for trial in range(5):
        payload.output.append(make_random_string())
        sock.send(payload.output[-1])
    for trial in range(5):
        payload.intake.append(sock.read())
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
            "security",
            "src",
            "server.py"
        )
        sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(cls.script_path))))
        random.seed()

    def test_compilation(self):
        compiled_path = compile(self.script_path)
        self.assertTrue(compiled_path)

    def test_text_io(self):
        from agutil.security import SecureServer
        server_payload = lambda x:None
        warnings.simplefilter('ignore', ResourceWarning)
        server_thread = None
        found_port = -1
        for port in range(4000, 10000):
            server_thread = threading.Thread(target=server_comms, args=(SecureServer, port, server_payload), name='Server thread', daemon=True)
            server_thread.start()
            server_thread.join(1)
            if server_thread.is_alive():
                found_port = port
                break
        warnings.resetwarnings()
        self.assertGreater(found_port, 3999, "Failed to bind to any ports on [4000, 10000]")
        client_payload = lambda x:None
        client_thread = threading.Thread(target=client_comms, args=(SecureServer, found_port, client_payload), daemon=True)
        client_thread.start()
        extra = 30 if TRAVIS else 0
        server_thread.join(60+extra)
        self.assertFalse(server_thread.is_alive(), "Server thread still running")
        client_thread.join(60+extra)
        self.assertFalse(client_thread.is_alive(), "Client thread still running")
        server_payload.sock.close()
        client_payload.sock.close()
        self.assertEqual(client_payload.comms_check, '+')
        self.assertEqual(len(server_payload.intake), len(client_payload.output))
        self.assertEqual(len(server_payload.output), len(client_payload.intake))
        self.assertListEqual(server_payload.intake, client_payload.output)
        self.assertListEqual(server_payload.output, client_payload.intake)
