import unittest
import os
from py_compile import compile
import sys
import random
import threading
import warnings
import tempfile
from filecmp import cmp
import time
import rsa

TRAVIS = 'CI' in os.environ

def make_random_string():
    return "".join(chr(random.randint(1,255)) for i in range(25))

def server_comms(fn, port, payload, pubkey, privkey):
    sock = fn('listen', port, 'password', defaultbits=1024, verbose=TRAVIS, _debug_keys=(pubkey, privkey))
    payload.intake=[]
    payload.output=[]
    for trial in range(5):
        payload.intake.append(sock.read())
        payload.output.append(make_random_string())
        sock.send(payload.output[-1])

def client_comms(_sockClass, port, payload, pubkey, privkey):
    sock = _sockClass('localhost', port, 'password', defaultbits=1024, verbose=TRAVIS, _debug_keys=(pubkey, privkey))
    payload.intake=[]
    payload.output=[]
    time.sleep(1)
    for trial in range(5):
        if TRAVIS:
            print("IO Cycle", trial)
        payload.output.append(make_random_string())
        sock.send(payload.output[-1])
        payload.intake.append(sock.read())
    sock.close()

def server_comms_files(fn, port, payload, directory, pubkey, privkey):
    sock = fn('listen', port, 'password', defaultbits=1024, verbose=TRAVIS, _debug_keys=(pubkey, privkey))
    payload.intake=[]
    payload.output=[]
    for trial in range(5):
        payload.intake.append(sock.savefile(
            tempfile.NamedTemporaryFile(dir=directory).name+".intake"
        ))
        writer = open(tempfile.NamedTemporaryFile(dir=directory).name+".output", mode='w')
        for line in range(5):
            writer.write(make_random_string()+"\n")
        writer.close()
        payload.output.append(writer.name)
        sock.sendfile(payload.output[-1])

def client_comms_files(_sockClass, port, payload, directory, pubkey, privkey):
    sock = _sockClass('localhost', port, 'password', defaultbits=1024, verbose=TRAVIS, _debug_keys=(pubkey, privkey))
    payload.intake=[]
    payload.output=[]
    time.sleep(1)
    for trial in range(5):
        if TRAVIS:
            print("IO Cycle", trial)
        writer = open(tempfile.NamedTemporaryFile(dir=directory).name+".output", mode='w')
        for line in range(5):
            writer.write(make_random_string()+"\n")
        writer.close()
        payload.output.append(writer.name)
        sock.sendfile(payload.output[-1])
        payload.intake.append(sock.savefile(tempfile.NamedTemporaryFile(dir=directory).name+".intake"))
    sock.close()

@unittest.skipIf(sys.platform.startswith("win"), "Pycrypto cannot compile on windows")
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
        (cls.pub, cls.priv) = rsa.newkeys(1024)

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
            server_thread = threading.Thread(target=server_comms, args=(new, port, server_payload, self.pub, self.priv), name='Server thread', daemon=True)
            server_thread.start()
            server_thread.join(1)
            if server_thread.is_alive():
                found_port = port
                break
        warnings.resetwarnings()
        self.assertGreater(found_port, 3999, "Failed to bind to any ports on [4000, 10000]")
        # self.assertIsInstance(ssWrapper.payload, SecureSocket, "Failed to bind to any ports on [4000, 10000]")
        client_payload = lambda x:None
        client_thread = threading.Thread(target=client_comms, args=(new, found_port, client_payload, self.pub, self.priv), name="Client thread", daemon=True)
        client_thread.start()
        runtime = None if TRAVIS else 45
        server_thread.join(runtime)
        self.assertFalse(server_thread.is_alive(), "Server thread still running")
        client_thread.join(runtime)
        self.assertFalse(client_thread.is_alive(), "Client thread still running")
        self.assertEqual(len(server_payload.intake), len(client_payload.output))
        self.assertEqual(len(server_payload.output), len(client_payload.intake))
        self.assertListEqual(server_payload.intake, client_payload.output)
        self.assertListEqual(server_payload.output, client_payload.intake)

    # @unittest.skipIf(TRAVIS, "Do not test File IO on travis")
    def test_files_io(self):
        from agutil.security import new
        from agutil.security import SecureSocket
        server_payload = lambda x:None
        warnings.simplefilter('ignore', ResourceWarning)
        server_thread = None
        found_port = -1
        directory = tempfile.TemporaryDirectory()
        # directory = lambda :None
        # directory.name = os.path.abspath("tests/security_output")
        for port in range(10000, 4000, -1):
            server_thread = threading.Thread(target=server_comms_files, args=(new, port, server_payload, directory.name, self.pub, self.priv), name='Server thread', daemon=True)
            server_thread.start()
            server_thread.join(1)
            if server_thread.is_alive():
                found_port = port
                break
        warnings.resetwarnings()
        self.assertGreater(found_port, 4000, "Failed to bind to any ports on [10000, 4000)")
        client_payload = lambda x:None
        client_thread = threading.Thread(target=client_comms_files, args=(new, found_port, client_payload, directory.name, self.pub, self.priv), name="Client thread", daemon=True)
        client_thread.start()
        runtime = None if TRAVIS else 45
        server_thread.join(runtime)
        self.assertFalse(server_thread.is_alive(), "Server thread still running")
        client_thread.join(runtime)
        self.assertFalse(client_thread.is_alive(), "Client thread still running")
        self.assertEqual(len(server_payload.intake), len(client_payload.output))
        self.assertEqual(len(server_payload.output), len(client_payload.intake))
        for i in range(len(server_payload.intake)):
            self.assertTrue(cmp(server_payload.intake[i], client_payload.output[i]))
            self.assertTrue(cmp(server_payload.output[i], client_payload.intake[i]))
        directory.cleanup()
