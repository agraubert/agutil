import unittest
import os
from py_compile import compile
import sys
import random
import tempfile
from filecmp import cmp
import rsa.randnum
import Crypto.Cipher.AES as AES

def make_random_string():
    return "".join(chr(random.randint(48,122)) for i in range(25))

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
            "files.py"
        )
        sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(cls.script_path))))
        random.seed()

    def test_compilation(self):
        compiled_path = compile(self.script_path)
        self.assertTrue(compiled_path)

    @unittest.skipIf(sys.platform.startswith('win'), "Tempfile cannot be used in this way on Windows")
    def test_encrypts_and_decrypts(self):
        from agutil.security import encryptFile, decryptFile
        for trial in range(5):
            source = tempfile.NamedTemporaryFile()
            encrypted = tempfile.NamedTemporaryFile()
            decrypted = tempfile.NamedTemporaryFile()
            aes_key = rsa.randnum.read_random_bits(256)
            aes_iv = rsa.randnum.read_random_bits(128)
            encryptionCipher = AES.new(aes_key, AES.MODE_CBC, aes_iv)
            decryptionCipher = AES.new(aes_key, AES.MODE_CBC, aes_iv)
            writer = open(source.name, mode='w')
            for line in range(15):
                writer.write(make_random_string())
                writer.write('\n')
            writer.close()
            encryptFile(source.name, encrypted.name, encryptionCipher)
            self.assertFalse(cmp(source.name, encrypted.name))
            decryptFile(encrypted.name, decrypted.name, decryptionCipher)
            self.assertTrue(cmp(source.name, decrypted.name))
