import unittest
import os
from py_compile import compile
import sys
import random

def make_random_string(length=25, lower=32, upper=127):
    return "".join(chr(random.randint(lower,upper)) for i in range(length))

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
            "protocols.py"
        )
        sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(cls.script_path))))
        random.seed()

    def test_compilation(self):
        compiled_path = compile(self.script_path)
        self.assertTrue(compiled_path)

    def test_int_byte_conversion(self):
        from agutil.security.src.protocols import intToBytes, bytesToInt
        for trial in range(25):
            num = random.randint(0, sys.maxsize)
            self.assertEqual(num, bytesToInt(intToBytes(num)))

    def test_padding_and_unpadding(self):
        from agutil.security.src.protocols import padstring, unpadstring
        for trial in range(25):
            text = make_random_string(random.randint(16, 4096))
            unpadded = unpadstring(padstring(text)).decode()
            self.assertEqual(len(text), len(unpadded))
            if len(text) <= 2048:
                self.assertEqual(text, unpadded)
            else:
                self.assertEqual(hash(text), hash(unpadded))

    def test_cmd_packing_and_unpacking(self):
        from agutil.security.src.protocols import packcmd, unpackcmd, _COMMANDS
        for cmd in _COMMANDS:
            data = {}
            num_keys = random.randint(0,15)
            for i in range(num_keys):
                key = make_random_string(random.randint(3,25), lower=59, upper=125)
                while key in data:
                    key = make_random_string(random.randint(3,25), lower=59, upper=125)
                if not i%10:
                    data[key] = True
                else:
                    data[key] = make_random_string(random.randint(1,4096))
            parsed = unpackcmd(packcmd(cmd, data))
            _cmd = _COMMANDS[parsed['cmd']]
            del parsed['cmd']
            self.assertEqual(cmd, _cmd)
            self.assertFalse({k for k in data} ^ {k for k in parsed})
            for key in data:
                self.assertEqual(len(data[key]), len(parsed[key]))
                if len(data[key]) <= 2048:
                    self.assertEqual(data[key], parsed[key])
                else:
                    self.assertEqual(hash(data[key]), hash(parsed[key]))
