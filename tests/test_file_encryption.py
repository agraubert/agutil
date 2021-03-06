import unittest
import unittest.mock
import os
from py_compile import compile
import sys
import random
import tempfile
from filecmp import cmp
import rsa.randnum
from hashlib import md5
import Cryptodome.Cipher.AES as AES
import warnings
from itertools import chain
import hashlib

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
        cls.test_data_dir = os.path.join(
            os.path.dirname(__file__),
            'data',
            'encryption'
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
            key = rsa.randnum.read_random_bits(256)
            writer = open(source, mode='w')
            for line in range(15):
                writer.write(make_random_string())
                writer.write('\n')
            writer.close()
            encryptFile(source, encrypted, key)
            self.assertFalse(cmp(source, encrypted))
            decryptFile(encrypted, decrypted, key)
            self.assertTrue(cmp(source, decrypted))
            os.remove(source)
            os.remove(encrypted)
            os.remove(decrypted)

    # @unittest.skipIf(sys.platform.startswith('win'), "Tempfile cannot be used in this way on Windows")
    def test_commands(self):
        import agutil.security.console
        warnings.simplefilter('ignore', DeprecationWarning)
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
                '-o',
                encrypted,
                '-p',
                "\"%s\""%password
            ])
            self.assertFalse(cmp(source, encrypted))
            agutil.security.console.main([
                'decrypt',
                encrypted,
                '-o',
                decrypted,
                '-p',
                "\"%s\""%password
            ])
            self.assertTrue(cmp(source, decrypted))
            with self.assertRaises(SystemExit):
                agutil.security.console.main([
                    'decrypt',
                    encrypted,
                    '-o',
                    decrypted,
                    '-p',
                    "\"%s\""%make_random_string()
                ])
            os.remove(source)
            os.remove(encrypted)
            os.remove(decrypted)
        warnings.resetwarnings()

    @unittest.skipIf(sys.version_info<(3,4), "This test is for python 3.4 and newer")
    def test_compatibility(self):
        #to ensure backwards compatibility
        #There must always be a way to decrypt the file, even as the api changes
        import agutil.security.console
        output_filename = tempname()
        agutil.security.console.main([
            'decrypt',
            os.path.join(
                self.test_data_dir,
                'encrypted'
            ),
            '-o',
            output_filename,
            '-l',
            '-p',
            'password'
        ])
        self.assertTrue(cmp(
            os.path.join(
                self.test_data_dir,
                'expected'
            ),
            output_filename
        ))
        os.remove(output_filename)

    @unittest.skipIf(sys.version_info<(3,4), "This test is for python 3.4 and newer")
    def test_platform_33_to_newer(self):
        #Test if a file encrypted on 3.3 can be decrypted on newer python versions using the --py33 flag
        import agutil.security.console
        output_filename = tempname()
        agutil.security.console.main([
            'decrypt',
            os.path.join(
                self.test_data_dir,
                'encrypted.3.3'
            ),
            '-o',
            output_filename,
            '--py33',
            '-p',
            'password'
        ])
        self.assertTrue(cmp(
            os.path.join(
                self.test_data_dir,
                'expected'
            ),
            output_filename
        ))
        os.remove(output_filename)

    @unittest.skipIf(sys.version_info>=(3,4), "This test is for python 3.3 and older")
    def test_platform_35_to_33(self):
        #Test if a file encrypted on 3.5 with the --py33 flag can be decrypted on python 3.3
        import agutil.security.console
        output_filename = tempname()
        agutil.security.console.main([
            'decrypt',
            os.path.join(
                self.test_data_dir,
                'encrypted.3.5'
            ),
            '-o',
            output_filename,
            '-p',
            'password'
        ])
        self.assertTrue(cmp(
            os.path.join(
                self.test_data_dir,
                'expected'
            ),
            output_filename
        ))
        os.remove(output_filename)

    @unittest.skipIf(sys.version_info<(3,4), "This test is for python 3.4 and newer")
    def test_modern_decryption(self):
        import agutil.security.console
        output_filename = tempname()
        agutil.security.console.main([
            'decrypt',
            os.path.join(
                self.test_data_dir,
                'modern'
            ),
            '-o',
            output_filename,
            '-p',
            'password'
        ])
        self.assertTrue(cmp(
            os.path.join(
                self.test_data_dir,
                'expected'
            ),
            output_filename
        ))
        os.remove(output_filename)

    def test_modern_decryption_33(self):
        import agutil.security.console
        output_filename = tempname()
        agutil.security.console.main([
            'decrypt',
            os.path.join(
                self.test_data_dir,
                'modern.3.3'
            ),
            '-o',
            output_filename,
            '-p',
            'password',
            '--py33'
        ])
        self.assertTrue(cmp(
            os.path.join(
                self.test_data_dir,
                'expected'
            ),
            output_filename
        ))
        os.remove(output_filename)

    def test_in_place(self):
        import agutil.security.console
        source = tempname()
        password = make_random_string()
        writer = open(source, mode='w')
        hasher = md5()
        for line in range(15):
            line = make_random_string() + '\n'
            writer.write(line)
            hasher.update(line.encode())
        writer.close()
        sourceHash = hasher.hexdigest()
        agutil.security.console.main([
            'encrypt',
            source,
            '-p',
            "\"%s\""%password
        ])
        agutil.security.console.main([
            'decrypt',
            source,
            '-p',
            "\"%s\""%password
        ])
        hasher = md5()
        reader = open(source, mode='rb')
        chunk = reader.read(1024)
        while chunk:
            hasher.update(chunk)
            chunk = reader.read(1024)
        reader.close()
        self.assertEqual(sourceHash, hasher.hexdigest())
        os.remove(source)

    def test_password_prompt(self):
        from io import StringIO
        import agutil.security.console
        password = make_random_string()
        mock = unittest.mock.create_autospec(agutil.security.console.getpass, return_value=password)
        agutil.security.console.getpass = mock
        source = tempname()
        encrypted = tempname()
        decrypted = tempname()
        writer = open(source, mode='w')
        for line in range(15):
            writer.write(make_random_string())
            writer.write('\n')
        writer.close()
        agutil.security.console.main([
            'encrypt',
            source,
            '-o',
            encrypted
        ])
        self.assertFalse(cmp(source, encrypted))
        agutil.security.console.main([
            'decrypt',
            encrypted,
            '-o',
            decrypted
        ])
        self.assertTrue(cmp(source, decrypted))
        mock.assert_has_calls([
            unittest.mock.call('Encryption password: '),
            unittest.mock.call('Confirm password: '),
            unittest.mock.call('Decryption password: ')
        ])

    def test_multi(self):
        import agutil.security.console
        encrypted = [tempname() for i in range(5)]
        decrypted = [tempname() for i in range(5)]
        password = make_random_string()
        source = []
        for i in range(5):
            source.append(tempname())
            writer = open(source[-1], mode='w')
            for line in range(15):
                writer.write(make_random_string())
                writer.write('\n')
            writer.close()
        agutil.security.console.main([
            'encrypt',
            ]+source+[
            ]+list(chain.from_iterable(zip(['-o']*5, encrypted)))+[
            '-p',
            "\"%s\""%password
        ])
        for (sourcefile, encryptedfile) in zip(source, encrypted):
            self.assertFalse(cmp(sourcefile, encryptedfile))
        agutil.security.console.main([
            'decrypt',
            ]+encrypted+[
            ]+list(chain.from_iterable(zip(['-o']*5, decrypted)))+[
            '-p',
            "\"%s\""%password
        ])
        for (sourcefile, decryptedfile) in zip(source, decrypted):
            self.assertTrue(cmp(sourcefile, decryptedfile))
        for filename in source:
            os.remove(filename)
        for filename in encrypted:
            os.remove(filename)
        for filename in decrypted:
            os.remove(filename)


    def test_multi_in_place(self):
        import agutil.security.console
        password = make_random_string()
        source = []
        hashes = []
        for i in range(5):
            source.append(tempname())
            hasher = md5()
            writer = open(source[-1], mode='w')
            for line in range(15):
                line = make_random_string()+'\n'
                writer.write(line)
                hasher.update(line.encode())
            writer.close()
            hashes.append(hasher.digest())
        agutil.security.console.main([
            'encrypt'
            ]+source+[
            '-p',
            "\"%s\""%password
        ])
        agutil.security.console.main([
            'decrypt',
            ]+source+[
            '-p',
            "\"%s\""%password
        ])
        for (filename, checksum) in zip(source, hashes):
            hasher = md5()
            reader = open(filename, mode='rb')
            chunk = reader.read(1024)
            while len(chunk):
                hasher.update(chunk)
                chunk = reader.read(1024)
            self.assertEqual(hasher.digest(), checksum)
            reader.close()
            os.remove(filename)
