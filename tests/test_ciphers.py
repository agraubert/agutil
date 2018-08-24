import unittest
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

key = b'\x91^\x86\x91`\xae\xb3n4\xf8\xca\xf1\x90iT\xc2\xb6`\xa99*\xect\x93\x84I\xe1}\xdc)\x8c\xa6'
legacy_key = b"\x9a1'W\n:\xda[\x18VZ\x94\xffm,\x9d\xd1\xb1Z9\xa0\x08\xc3q&\xec><\x10\x10\x1e\xa6"

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
            "cipher.py"
        )
        cls.header_path = os.path.join(
            os.path.dirname(
                os.path.dirname(
                    os.path.abspath(__file__)
                )
            ),
            "agutil",
            "security",
            "src",
            "cipher_header.py"
        )
        cls.test_data_dir = os.path.join(
            os.path.dirname(__file__),
            'data',
            'encryption'
        )
        sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(cls.script_path))))
        random.seed()

    def test_compilation(self):
        compiled_path = compile(self.header_path)
        self.assertTrue(compiled_path)
        compiled_path = compile(self.script_path)
        self.assertTrue(compiled_path)

    def test_bitmasks(self):
        from agutil.security.src.cipher import Bitmask
        for trial in range(15):
            mask = Bitmask()
            n = 0
            for bit in range(random.randint(0,7)):
                bit = random.randint(0,7)
                current = bool(n & (1 << bit))
                self.assertEqual(mask[bit], current)
                mask[bit] = True
                n = n | (1 << bit)
                current = bool(n & (1 << bit))
                self.assertEqual(mask[bit], current)
            self.assertEqual(mask.mask.data, n)

    def test_exceptions(self):
        from agutil.security.src.cipher import HeaderLengthError, EncryptionCipher, DecryptionCipher
        source = os.urandom(1024 * random.randint(1,16))
        key = os.urandom(32)
        encryptor = EncryptionCipher(key)
        data = encryptor.encrypt(source) + encryptor.finish()
        with self.assertRaises(HeaderLengthError):
            decryptor = DecryptionCipher(data[:24], key)

    def test_all_ciphers(self):
        from agutil.security.src.cipher import EncryptionCipher, DecryptionCipher
        from Cryptodome.Cipher import AES
        ciphers = {
            AES.MODE_ECB, AES.MODE_CBC, AES.MODE_CTR, AES.MODE_CFB,
            AES.MODE_OFB, AES.MODE_OPENPGP, AES.MODE_CCM, AES.MODE_EAX,
            AES.MODE_GCM, AES.MODE_SIV, AES.MODE_OCB
        }
        for cipher in ciphers:
            source = os.urandom(1024 * random.randint(1,16))
            key = os.urandom(32)
            encryptor = EncryptionCipher(
                key,
                cipher_type=cipher
            )
            data = encryptor.encrypt(source) + encryptor.finish()
            self.assertNotEqual(source, data)
            decryptor = DecryptionCipher(data[:64], key)
            compare = decryptor.decrypt(data[64:]) + decryptor.finish()
            self.assertEqual(source, compare)
            if cipher <= AES.MODE_OPENPGP:
                source = os.urandom(1024 * random.randint(1,16))
                key = os.urandom(32)
                encryptor = EncryptionCipher(
                    key,
                    secondary_cipher_type=cipher,
                    use_legacy_ciphers=True,
                )
                data = encryptor.encrypt(source) + encryptor.finish()
                self.assertNotEqual(source, data)
                decryptor = DecryptionCipher(data[:64], key)
                compare = decryptor.decrypt(data[64:]) + decryptor.finish()
                self.assertEqual(source, compare)

                source = os.urandom(1024 * random.randint(1,16))
                key = os.urandom(32)
                encryptor = EncryptionCipher(
                    key,
                    secondary_cipher_type=cipher,
                    encrypted_nonce=True
                )
                data = encryptor.encrypt(source) + encryptor.finish()
                self.assertNotEqual(source, data)
                decryptor = DecryptionCipher(data[:64], key)
                compare = decryptor.decrypt(data[64:]) + decryptor.finish()
                self.assertEqual(source, compare)

    def test_encryption_decryption(self):
        from agutil.security.src.cipher import configure_cipher, EncryptionCipher, DecryptionCipher
        for trial in range(5):
            source = os.urandom(1024 * random.randint(1,16))
            key = os.urandom(32)
            encryptor = EncryptionCipher(key)
            data = encryptor.encrypt(source) + encryptor.finish()
            self.assertNotEqual(source, data)
            decryptor = DecryptionCipher(data[:64], key)
            compare = decryptor.decrypt(data[64:]) + decryptor.finish()
            self.assertEqual(source, compare)
            encryptor = EncryptionCipher(
                key,
                use_legacy_ciphers=True
            )
            self.assertEqual(encryptor.header_buffer[:16], encryptor.header.data)
            data = encryptor.encrypt(source) + encryptor.finish()
            self.assertNotEqual(source, data)
            decryptor = DecryptionCipher(data[:64], key)
            compare = decryptor.decrypt(data[64:]) + decryptor.finish()
            self.assertEqual(source, compare)
            encryptor = EncryptionCipher(
                key,
                enable_compatability=True
            )
            self.assertNotEqual(encryptor.header_buffer[:16], encryptor.header.data)
            data = encryptor.encrypt(source) + encryptor.finish()
            self.assertNotEqual(source, data)
            decryptor = DecryptionCipher(data[:64], key)
            compare = decryptor.decrypt(data[64:]) + decryptor.finish()
            self.assertEqual(source, compare)

    def test_bulk(self):
        from agutil.security.src.cipher import configure_cipher, EncryptionCipher, DecryptionCipher
        for trial in range(5):
            source = os.urandom(1024 * random.randint(1,16))
            key = os.urandom(32)
            encryptor = EncryptionCipher(
                key,
                enable_streaming=False
            )
            header_len = len(encryptor.header_buffer)
            data = encryptor.encrypt(source)
            self.assertEqual(len(data), header_len)
            data += encryptor.finish()
            self.assertNotEqual(source, data)
            decryptor = DecryptionCipher(data[:64], key)
            compare = decryptor.decrypt(data[64:]) + decryptor.finish()
            self.assertEqual(source, compare)

    def test_inline(self):
        from agutil.security.src.cipher import configure_cipher, EncryptionCipher, DecryptionCipher
        for trial in range(5):
            source = os.urandom(1024 * random.randint(1,16))
            key = os.urandom(32)
            encryptor = EncryptionCipher(key)
            decryptor = DecryptionCipher(
                encryptor.encrypt(source) + encryptor.finish(),
                key
            )
            compare = decryptor.decrypt() + decryptor.finish()
            self.assertEqual(source, compare)

    def test_external_nonce(self):
        from agutil.security.src.cipher import configure_cipher, EncryptionCipher, DecryptionCipher
        for trial in range(5):
            source = os.urandom(1024 * random.randint(1,16))
            key = os.urandom(32)
            nonce = os.urandom(16)
            encryptor = EncryptionCipher(
                key,
                nonce,
                store_nonce=False
            )
            self.assertNotIn(nonce, encryptor.header_buffer)
            data = encryptor.encrypt(source) + encryptor.finish()
            self.assertNotEqual(source, data)
            decryptor = DecryptionCipher(data[:64], key, encryptor.nonce)
            compare = decryptor.decrypt(data[64:]) + decryptor.finish()
            self.assertEqual(source, compare)

    def test_encrypted_nonce(self):
        from agutil.security.src.cipher import configure_cipher, EncryptionCipher, DecryptionCipher
        for trial in range(5):
            source = os.urandom(1024 * random.randint(1,16))
            key = os.urandom(32)
            nonce = os.urandom(16)
            encryptor = EncryptionCipher(
                key,
                nonce,
                encrypted_nonce=True
            )
            self.assertNotEqual(nonce, encryptor.header_buffer[-16:])
            data = encryptor.encrypt(source) + encryptor.finish()
            self.assertNotEqual(source, data)
            decryptor = DecryptionCipher(data[:64], key)
            compare = decryptor.decrypt(data[64:]) + decryptor.finish()
            self.assertEqual(source, compare)
            encryptor = EncryptionCipher(
                key,
                nonce,
                encrypted_nonce=True,
                legacy_randomized_nonce=True,
                legacy_store_nonce=False
            )
            self.assertNotEqual(nonce, encryptor.header_buffer[-16:])
            data = encryptor.encrypt(source) + encryptor.finish()
            self.assertNotEqual(source, data)
            decryptor = DecryptionCipher(data[:64], key)
            compare = decryptor.decrypt(data[64:]) + decryptor.finish()
            self.assertEqual(source, compare)
            source = os.urandom(1024 * random.randint(1,16))
            key = os.urandom(32)
            nonce = os.urandom(16)
            encryptor = EncryptionCipher(
                key,
                nonce,
                encrypted_nonce=True,
                encrypted_tag=True
            )
            self.assertNotEqual(nonce, encryptor.header_buffer[-16:])
            data = encryptor.encrypt(source) + encryptor.finish()
            self.assertNotEqual(source, data)
            decryptor = DecryptionCipher(data[:64], key)
            compare = decryptor.decrypt(data[64:]) + decryptor.finish()
            self.assertEqual(source, compare)

    def test_legacy_decryption(self):
        from agutil.security.src.cipher import DecryptionCipher
        with open(os.path.join(self.test_data_dir, 'expected'), 'rb') as r:
            expected = r.read()
        with open(os.path.join(self.test_data_dir, 'legacy'), 'rb') as r:
            cipher = DecryptionCipher(
                r.read(),
                key,
            )
        self.assertEqual(expected, cipher.decrypt() + cipher.finish())
        with open(os.path.join(self.test_data_dir, 'encrypted'), 'rb') as r:
            cipher = DecryptionCipher(
                r.read(),
                key,
                legacy_force=True
            )
        self.assertEqual(expected, cipher.decrypt() + cipher.finish())
        with open(os.path.join(self.test_data_dir, 'encrypted.3.3'), 'rb') as r:
            cipher = DecryptionCipher(
                r.read(),
                legacy_key,
            )
        self.assertEqual(expected, cipher.decrypt() + cipher.finish())
        with open(os.path.join(self.test_data_dir, 'encrypted.3.5'), 'rb') as r:
            cipher = DecryptionCipher(
                r.read(),
                legacy_key,
            )
        self.assertEqual(expected, cipher.decrypt() + cipher.finish())
