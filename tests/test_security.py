import unittest
import os
from py_compile import compile
import sys
import random
import threading
import warnings
import tempfile
import os

TRAVIS = 'CI' in os.environ

def make_random_string():
    return "".join(chr(random.randint(48,122)) for i in range(25))

def make_random_file(filename):
    writer = open(filename, mode='w')
    contents = '\n'.join(make_random_string() for _ in range(25))
    writer.write(contents)
    writer.close()
    return contents

def server_comms(secureClass, port, payload):
    ss = secureClass(port, password='password', rsabits=1024)
    sock = ss.accept()
    payload.intake=[]
    payload.output=[]
    ss.close()
    sock.sock.sendRAW("+")
    for trial in range(5):
        payload.output.append(make_random_string())
        sock.send(payload.output[-1])
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
        payload.intake.append(sock.read())
    payload.sock = sock

def server_comms_files(secureClass, port, payload):
    ss = secureClass(port, password='password', rsabits=1024)
    sock = ss.accept()
    payload.intake=[]
    payload.output=[]
    ss.close()
    sock.sock.sendRAW("+")
    for trial in range(5):
        outfile = tempfile.NamedTemporaryFile()
        infile = tempfile.NamedTemporaryFile()
        sock.savefile(infile.name, force=True)
        reader = open(infile.name, mode='r')
        payload.intake.append(reader.read())
        reader.close()
        payload.output.append(make_random_file(outfile.name))
        sock.sendfile(outfile.name)
        sock.sock.recvRAW()
    payload.sock = sock

def client_comms_files(secureclass, port, payload):
    sock = secureclass('localhost', port, password='password', rsabits=1024, verbose=False)
    payload.intake=[]
    payload.output=[]
    payload.comms_check = sock.sock.recvRAW(decode=True)
    for trial in range(5):
        outfile = tempfile.NamedTemporaryFile()
        infile = tempfile.NamedTemporaryFile()
        payload.output.append(make_random_file(outfile.name))
        sock.sendfile(outfile.name)
        sock.savefile(infile.name, force=True)
        sock.sock.sendRAW('+')
        reader = open(infile.name, mode='r')
        payload.intake.append(reader.read())
        reader.close()
    payload.sock = sock

class test(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.connection_script_path = os.path.join(
            os.path.dirname(
                os.path.dirname(
                    os.path.abspath(__file__)
                )
            ),
            "agutil",
            "security",
            "src",
            "connection.py"
        )
        cls.server_script_path = os.path.join(
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
        sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(cls.connection_script_path))))
        random.seed()

    def test_compilation(self):
        compiled_path = compile(self.connection_script_path)
        self.assertTrue(compiled_path)
        compiled_path = compile(self.server_script_path)
        self.assertTrue(compiled_path)

    def test_text_io(self):
        from agutil.security import SecureConnection, SecureServer
        server_payload = lambda x:None
        warnings.simplefilter('ignore', ResourceWarning)
        server_thread = None
        found_port = -1
        for port in range(6000, 7000):
            server_thread = threading.Thread(target=server_comms, args=(SecureServer, port, server_payload), name='Server thread', daemon=True)
            server_thread.start()
            server_thread.join(1)
            if server_thread.is_alive():
                found_port = port
                break
        warnings.resetwarnings()
        self.assertGreater(found_port, 5999, "Failed to bind to any ports on [6000, 7000]")
        client_payload = lambda x:None
        client_thread = threading.Thread(target=client_comms, args=(SecureConnection, found_port, client_payload), daemon=True)
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

    def test_files_io(self):
        from agutil.security import SecureConnection, SecureServer
        server_payload = lambda x:None
        warnings.simplefilter('ignore', ResourceWarning)
        server_thread = None
        found_port = -1
        for port in range(7000, 8000):
            server_thread = threading.Thread(target=server_comms_files, args=(SecureServer, port, server_payload), name='Server thread', daemon=True)
            server_thread.start()
            server_thread.join(1)
            if server_thread.is_alive():
                found_port = port
                break
        warnings.resetwarnings()
        self.assertGreater(found_port, 6999, "Failed to bind to any ports on [7000, 8000]")
        client_payload = lambda x:None
        client_thread = threading.Thread(target=client_comms_files, args=(SecureConnection, found_port, client_payload), daemon=True)
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
