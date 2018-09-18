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

def server_comms(secureclass, queueclass, ss, payload):
    global startup_lock
    startup_lock.release()
    try:
        sock = ss.accept(secureclass, rsabits=1024)
        payload.exception1 = False
    except ValueError:
        payload.exception1 = True
    try:
        sock = ss.accept(secureclass, rsabits=1024)
        payload.exception2 = False
    except ValueError:
        payload.exception2 = True
    sock = ss.accept(secureclass, rsabits=1024)
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
    sock = queueclass('localhost', port)
    sock.send('<potato>', '__protocol__')
    sock.close()
    try:
        sock = secureclass('localhost', port, rsabits=1024, password="potato")
        payload.exception = False
    except ValueError:
        payload.exception = True
    sock = secureclass('localhost', port, rsabits=1024)
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
        server_thread = threading.Thread(target=server_comms, args=(SecureSocket, QueuedSocket, ss, server_payload), daemon=True)
        client_thread = threading.Thread(target=client_comms, args=(SecureSocket, QueuedSocket, Socket, ss.port, client_payload), daemon=True)
        server_thread.start()
        client_thread.start()
        extra = 30 if TRAVIS else 0
        server_thread.join(60+extra)
        self.assertFalse(server_thread.is_alive(), "Server thread still running")
        client_thread.join(60+extra)
        self.assertFalse(client_thread.is_alive(), "Client thread still running")
        self.assertRaises(TypeError, client_payload.sock.sendRAW, 13, 'test')
        self.assertRaises(TypeError, client_payload.sock.send, 13, 'test')
        self.assertRaises(TypeError, client_payload.sock.sendAES, 13)
        self.assertRaises(TypeError, client_payload.sock.sendAES, 'blorg', 'test', 13)
        self.assertRaises(TypeError, client_payload.sock.sendAES, 'blorg', 'test', True, 13)
        server_payload.sock.close()
        client_payload.sock.close()
        self.assertTrue(server_payload.exception1)
        self.assertTrue(server_payload.exception2)
        self.assertTrue(client_payload.exception)
        self.assertEqual(len(server_payload.intake), len(client_payload.output))
        self.assertEqual(len(server_payload.output), len(client_payload.intake))
        self.assertListEqual(server_payload.intake, client_payload.output)
        self.assertListEqual(server_payload.output, client_payload.intake)
        self.assertRaises(IOError, client_payload.sock.send, "fish")
