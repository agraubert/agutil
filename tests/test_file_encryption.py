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
    return "".join(chr(random.randint(0,255)) for i in range(25))

def tempname():
    (handle, name) = tempfile.mkstemp()
    os.close(handle)
    return name

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

    # @unittest.skipIf(sys.platform.startswith('win'), "Tempfile cannot be used in this way on Windows")
    def test_encrypts_and_decrypts(self):
        from agutil.security import encryptFile, decryptFile
        for trial in range(5):
            source = tempname()
            encrypted = tempname()
            decrypted = tempname()
            aes_key = rsa.randnum.read_random_bits(256)
            aes_iv = rsa.randnum.read_random_bits(128)
            encryptionCipher = AES.new(aes_key, AES.MODE_CBC, aes_iv)
            decryptionCipher = AES.new(aes_key, AES.MODE_CBC, aes_iv)
            writer = open(source, mode='w')
            for line in range(15):
                writer.write(make_random_string())
                writer.write('\n')
            writer.close()
            encryptFile(source, encrypted, encryptionCipher)
            self.assertFalse(cmp(source, encrypted))
            decryptFile(encrypted, decrypted, decryptionCipher)
            self.assertTrue(cmp(source, decrypted))
            os.remove(source)
            os.remove(encrypted)
            os.remove(decrypted)

    # @unittest.skipIf(sys.platform.startswith('win'), "Tempfile cannot be used in this way on Windows")
    def test_commands(self):
        import agutil.security.console
        for trial in range(5):
            source = tempname()
            encrypted = tempname()
            decrypted = tempname()
            password = make_random_string()
            writer = open(source, mode='w')
            for line in range(15):
                writer.write(make_random_string())
                writer.write('\n')
            writer.close()
            agutil.security.console.main([
                'encrypt',
                source,
                encrypted,
                "\"%s\""%password
            ])
            self.assertFalse(cmp(source, encrypted))
            agutil.security.console.main([
                'decrypt',
                encrypted,
                decrypted,
                "\"%s\""%password
            ])
            self.assertTrue(cmp(source, decrypted))
            os.remove(source)
            os.remove(encrypted)
            os.remove(decrypted)

    def test_chunk_encryption_decryption(self):
        from agutil.security.src.files import _encrypt_chunk, _decrypt_chunk
        for trial in range(5):
            source = "".join(make_random_string() for _ in range(1, 200))
            aes_key = rsa.randnum.read_random_bits(256)
            aes_iv = rsa.randnum.read_random_bits(128)
            encryptionCipher = AES.new(aes_key, AES.MODE_CBC, aes_iv)
            decryptionCipher = AES.new(aes_key, AES.MODE_CBC, aes_iv)
            decrypted = _decrypt_chunk(_encrypt_chunk(source, encryptionCipher), decryptionCipher).decode()
            self.assertEqual(len(source), len(decrypted))
            if len(source) <= 2048:
                self.assertEqual(source, decrypted)
            else:
                self.assertEqual(hash(source), hash(decrypted))
