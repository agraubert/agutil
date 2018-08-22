import unittest
import os
from py_compile import compile
import sys
import random
import threading
import warnings
import tempfile
import os
import time
import io
import port_for as pf
from .utils import TempDir

TRAVIS = 'CI' in os.environ

tempname = None #Bad practice...

def make_random_string():
    return "".join(chr(random.randint(0,255)) for i in range(25))

def make_random_file(filename):
    writer = open(filename, mode='w')
    contents = '\n'.join(make_random_string() for _ in range(25))
    writer.write(contents)
    writer.close()
    return contents

def server_comms(secureClass, port, payload):
    ss = secureClass(port, password='password', rsabits=1024)
    try:
        sock = ss.accept()
        payload.exception = False
    except ValueError:
        payload.exception = True
    sock = ss.accept()
    payload.intake=[]
    payload.output=[]
    confirmations = []
    ss.close()
    sock.sock.sendRAW("+")
    for trial in range(5):
        payload.output.append(make_random_string())
        confirmations.append(sock.send(payload.output[-1]))
        payload.intake.append(sock.read())
    for conf in confirmations:
        sock.confirm(conf)
    payload.sock = sock

def client_comms(secureclass, securesocketclass, port, payload):
    sock = securesocketclass('localhost', port, password='password', rsabits=1024)
    sock.sendRAW('<potato>', '__protocol__')
    sock.close()
    sock = secureclass('localhost', port, password='password', rsabits=1024)
    payload.intake=[]
    payload.output=[]
    confirmations = []
    payload.comms_check = sock.sock.recvRAW(decode=True)
    for trial in range(5):
        payload.output.append(make_random_string())
        confirmations.append(sock.send(payload.output[-1]))
        payload.intake.append(sock.read())
    for conf in confirmations:
        sock.confirm(conf)
    payload.sock = sock

def server_comms_files(secureClass, port, payload):
    try:
        ss = secureClass(port, password='password', rsabits=1024)
        try:
            sock = ss.accept()
            payload.exception = False
        except ValueError:
            payload.exception = True
        sock = ss.accept()
        payload.intake=[]
        payload.output=[]
        ss.close()
        sock.sock.sendRAW("+")
        for trial in range(5):
            outfile = tempname()
            infile = tempname()
            sock.savefile(infile, force=True)
            reader = open(infile, mode='rb')
            payload.intake.append(reader.read().decode())
            reader.close()
            payload.output.append(make_random_file(outfile))
            sock.sendfile(outfile)
            sock.sock.recvRAW()
            os.remove(outfile)
            os.remove(infile)
        outfile = tempname()
        payload.output.append(make_random_file(outfile))
        sock.sendfile(outfile)
        sock.sock.recvRAW()
        os.remove(outfile)
        payload.sock = sock
    except:
        print("SERR", sock.sock.queue)
        raise

def client_comms_files(secureclass, port, payload):
    try:
        try:
            sock = secureclass('localhost', port, password='wrong password', rsabits=1024)
            payload.exception = False
        except ValueError:
            payload.exception = True
        sock = secureclass('localhost', port, password='password', rsabits=1024)
        payload.intake=[]
        payload.output=[]
        payload.comms_check = sock.sock.recvRAW(decode=True)
        for trial in range(5):
            outfile = tempname()
            infile = tempname()
            payload.output.append(make_random_file(outfile))
            sock.sendfile(outfile)
            sock.savefile(infile, force=True)
            sock.sock.sendRAW('+')
            reader = open(infile, mode='rb')
            payload.intake.append(reader.read().decode())
            reader.close()
            os.remove(outfile)
            os.remove(infile)
        sys.stdout = open(os.devnull, 'w')
        infile = tempname()
        sys.stdin = io.StringIO("y"+os.linesep)
        sock.savefile(infile)
        sock.sock.sendRAW("+")
        reader = open(infile, mode='rb')
        payload.intake.append(reader.read().decode())
        reader.close()
        sys.stdout.close()
        sys.stdout = sys.__stdout__
        sys.stdin.close()
        sys.stdin = sys.__stdin__
        os.remove(infile)
        payload.sock = sock
    except:
        print("CERR", sock.sock.queue)
        raise

class test(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        global tempname
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
        cls.test_dir = TempDir()
        tempname = cls.test_dir

    def test_compilation(self):
        compiled_path = compile(self.connection_script_path)
        self.assertTrue(compiled_path)
        compiled_path = compile(self.server_script_path)
        self.assertTrue(compiled_path)

    def test_text_io(self):
        from agutil.security import SecureConnection, SecureServer, SecureSocket
        server_payload = lambda x:None
        warnings.simplefilter('ignore', ResourceWarning)
        server_thread = None
        found_port = -1
        for attempt in range(10):
            found_port = pf.select_random()
            server_thread = threading.Thread(target=server_comms, args=(SecureServer, found_port, server_payload), name='Server thread', daemon=True)
            server_thread.start()
            server_thread.join(1)
            if server_thread.is_alive():
                break
        warnings.resetwarnings()
        self.assertTrue(server_thread.is_alive(), "Failed to bind to any ports after 10 attempts")
        client_payload = lambda x:None
        client_thread = threading.Thread(target=client_comms, args=(SecureConnection, SecureSocket, found_port, client_payload), daemon=True)
        client_thread.start()
        extra = 30 if TRAVIS else 0
        server_thread.join(60+extra)
        self.assertFalse(server_thread.is_alive(), "Server thread still running")
        client_thread.join(60+extra)
        self.assertFalse(client_thread.is_alive(), "Client thread still running")
        self.assertRaises(TypeError, client_payload.sock.send, 13)
        server_payload.sock.close()
        time.sleep(.25)
        client_payload.sock.close()
        self.assertEqual(client_payload.comms_check, '+')
        self.assertTrue(server_payload.exception)
        # self.assertTrue(client_payload.exception)
        self.assertEqual(len(server_payload.intake), len(client_payload.output))
        self.assertEqual(len(server_payload.output), len(client_payload.intake))
        self.assertListEqual(server_payload.intake, client_payload.output)
        self.assertListEqual(server_payload.output, client_payload.intake)
        self.assertRaises(IOError, client_payload.sock.send, 'fish')
        self.assertRaises(IOError, client_payload.sock.read)

    # @unittest.skipIf(sys.platform.startswith('win'), "Tempfile cannot be used in this way on windows")
    def test_files_io(self):
        from agutil.security import SecureConnection, SecureServer
        server_payload = lambda x:None
        warnings.simplefilter('ignore', ResourceWarning)
        server_thread = None
        found_port = -1
        for attempt in range(10):
            found_port = pf.select_random()
            server_thread = threading.Thread(target=server_comms_files, args=(SecureServer, found_port, server_payload), name='Server thread', daemon=True)
            server_thread.start()
            server_thread.join(1)
            if server_thread.is_alive():
                break
        warnings.resetwarnings()
        self.assertTrue(server_thread.is_alive(), "Failed to bind to any ports after 10 attempts")
        client_payload = lambda x:None
        client_thread = threading.Thread(target=client_comms_files, args=(SecureConnection, found_port, client_payload), daemon=True)
        client_thread.start()
        extra = 30 if TRAVIS else 0
        server_thread.join(60+extra)
        self.assertFalse(server_thread.is_alive(), "Server thread still running")
        client_thread.join(60+extra)
        self.assertFalse(client_thread.is_alive(), "Client thread still running")
        self.assertRaises(FileNotFoundError, client_payload.sock.sendfile, 'blarg')
        server_payload.sock.close()
        time.sleep(.25)
        client_payload.sock.close()
        self.assertEqual(client_payload.comms_check, '+')
        self.assertTrue(server_payload.exception)
        self.assertTrue(client_payload.exception)
        self.assertEqual(len(server_payload.intake), len(client_payload.output))
        self.assertEqual(len(server_payload.output), len(client_payload.intake))
        for i in range(len(server_payload.intake)):
            self.assertEqual(len(server_payload.intake[i]), len(client_payload.output[i]))
            if len(server_payload.intake[i])>2048:
                self.assertEqual(hash(server_payload.intake[i]), hash(client_payload.output[i]))
            else:
                self.assertEqual(server_payload.intake[i], client_payload.output[i])
        for i in range(len(client_payload.intake)):
            self.assertEqual(len(client_payload.intake[i]), len(server_payload.output[i]))
            if len(client_payload.intake[i])>2048:
                self.assertEqual(hash(client_payload.intake[i]), hash(server_payload.output[i]))
            else:
                self.assertEqual(client_payload.intake[i], server_payload.output[i])
        self.assertRaises(IOError, client_payload.sock.sendfile, 'fish')
        self.assertRaises(IOError, client_payload.sock.savefile, 'fish')
