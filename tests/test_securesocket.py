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

def make_random_string():
    return "".join(chr(random.randint(0,255)) for i in range(25))

def server_comms(secureclass, queueclass, ss, payload):
    global startup_lock
    startup_lock.release()
    sock = secureclass(ss.accept(), rsabits=1024, verbose=False)
    ss.close()
    payload.intake=[]
    payload.output=[]
    for trial in range(5):
        if trial%2:
            payload.intake.append(sock.recvAES(decode=True))
            payload.output.append(make_random_string())
            sock.sendAES(payload.output[-1], key=True, iv=True)
        else:
            payload.intake.append(sock.recvRSA(decode=True))
            payload.output.append(make_random_string())
            sock.sendRSA(payload.output[-1])
    payload.sock = sock

def client_comms(secureclass, queueclass, _sockClass, port, payload):
    global startup_lock
    startup_lock.acquire()
    startup_lock.release()
    sock = secureclass(_sockClass('localhost', port), rsabits=1024, verbose=False)
    payload.intake=[]
    payload.output=[]
    for trial in range(5):
        if trial%2:
            payload.output.append(make_random_string())
            sock.sendAES(payload.output[-1], key=True, iv=True)
            payload.intake.append(sock.recvAES(decode=True))
        else:
            payload.output.append(make_random_string())
            sock.sendRSA(payload.output[-1])
            payload.intake.append(sock.recvRSA(decode=True))
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
            "securesocket.py"
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
        from agutil.security import SecureSocket
        ss = None
        warnings.simplefilter('ignore', ResourceWarning)
        for port in range(5000, 6000):
            try:
                ss = SocketServer(port)
            except OSError:
                if ss!=None:
                    ss.close()
            if ss!=None:
                break
        warnings.resetwarnings()
        self.assertIsInstance(ss, SocketServer, "Failed to bind to any ports on [5000, 6000]")
        startup_lock.acquire()
        server_payload = lambda x:None
        client_payload = lambda x:None
        server_thread = threading.Thread(target=server_comms, args=(SecureSocket, QueuedSocket, ss, server_payload), daemon=True)
        client_thread = threading.Thread(target=client_comms, args=(SecureSocket, QueuedSocket, Socket, ss.port, client_payload), daemon=True)
        server_thread.start()
        client_thread.start()
        extra = 30 if TRAVIS else 0
        server_thread.join(60+extra)
        self.assertFalse(server_thread.is_alive(), "Server thread still running")
        client_thread.join(60+extra)
        self.assertFalse(client_thread.is_alive(), "Client thread still running")
        server_payload.sock.close()
        client_payload.sock.close()
        self.assertEqual(len(server_payload.intake), len(client_payload.output))
        self.assertEqual(len(server_payload.output), len(client_payload.intake))
        self.assertListEqual(server_payload.intake, client_payload.output)
        self.assertListEqual(server_payload.output, client_payload.intake)
