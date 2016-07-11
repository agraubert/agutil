import unittest
import os
from py_compile import compile
import sys
import random
import threading
import warnings

def text_client():
    pass

def make_random_string():
    return "".join(chr(random.randint(0,255)) for i in range(25))

def server_comms(fn, port, payload):
    sock = fn('listen', port, defaultbits=1024)
    payload.intake=[]
    payload.output=[]
    for trial in range(5):
        print('=====================================')
        print("IO CYCLE", trial)
        payload.intake.append(sock.read())
        payload.output.append(make_random_string())
        sock.send(payload.output[-1])
    sock.close()

def client_comms(_sockClass, port, payload):
    sock = _sockClass('localhost', port, defaultbits=1024)
    payload.intake=[]
    payload.output=[]
    for trial in range(5):
        payload.output.append(make_random_string())
        sock.send(payload.output[-1])
        payload.intake.append(sock.read())
    sock.close()

class test(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.source_dir = os.path.join(
            os.path.dirname(
                os.path.dirname(
                    os.path.abspath(__file__)
                )
            ),
            "agutil",
            "security",
            "src"
        )
        sys.path.append(os.path.dirname(os.path.dirname(cls.source_dir)))
        random.seed()

    def test_compilation(self):
        core_path = compile(os.path.join(
            self.source_dir,
            "core.py"
        ))
        channel_path = compile(os.path.join(
            self.source_dir,
            "channel.py"
        ))
        protocols_path = compile(os.path.join(
            self.source_dir,
            "protocols.py"
        ))
        self.assertTrue(core_path, "core.py compilation error")
        self.assertTrue(channel_path, "channel.py compilation error")
        self.assertTrue(protocols_path, "protocols.py compilation error")

    def test_text_io(self):
        from agutil.security import new
        from agutil.security import SecureSocket
        server_payload = lambda x:None
        warnings.simplefilter('ignore', ResourceWarning)
        server_thread = None
        found_port = -1
        for port in range(4000, 10000):
            server_thread = threading.Thread(target=server_comms, args=(new, port, server_payload))
            server_thread.start()
            server_thread.join(1)
            if server_thread.is_alive():
                found_port = port
                break
        warnings.resetwarnings()
        self.assertGreater(found_port, 3999, "Failed to bind to any ports on [4000, 10000]")
        # self.assertIsInstance(ssWrapper.payload, SecureSocket, "Failed to bind to any ports on [4000, 10000]")
        client_payload = lambda x:None
        client_thread = threading.Thread(target=client_comms, args=(new, found_port, client_payload))
        client_thread.start()
        server_thread.join()
        self.assertFalse(server_thread.is_alive(), "Server thread still running")
        client_thread.join()
        self.assertFalse(client_thread.is_alive(), "Client thread still running")
        self.assertEqual(len(server_payload.intake), len(client_payload.output))
        self.assertEqual(len(server_payload.output), len(client_payload.intake))
        self.assertListEqual(server_payload.intake, client_payload.output)
        self.assertListEqual(server_payload.output, client_payload.intake)

    def test_connection_with_password(self):
        pass

    def test_files_io(self):
        pass
