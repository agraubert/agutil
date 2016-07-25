import unittest
import os
from py_compile import compile
import sys
import random

def make_random_string(length=25, lower=0, upper=255):
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
            "src",
            "misc.py"
        )
        sys.path.append(os.path.dirname(os.path.dirname(cls.script_path)))
        random.seed()

    def test_compilation(self):
        compiled_path = compile(self.script_path)
        self.assertTrue(compiled_path)

    def test_sequence_splitting(self):
        from agutil import split_iterable
        for trial in range(25):
            sequence = make_random_string(random.randint(10,10000))
            sequence_length = len(sequence)
            total = 0
            split = random.randint(5,sequence_length-1)
            for subsequence in split_iterable(sequence, split):
                subsequence_text = [char for char in subsequence]
                subsequence_length = len(subsequence_text)
                self.assertEqual(subsequence_length, min(split, sequence_length-total))
                if subsequence_length <= 2048:
                    self.assertEqual(sequence[total:total+split], ''.join(subsequence_text))
                else:
                    self.assertEqual(hash(sequence[total:total+split]), hash(''.join(subsequence_text)))
                total += subsequence_length
                self.assertLessEqual(total, sequence_length)
            self.assertEqual(total, sequence_length)

    def test_byte_xor(self):
        from agutil import byte_xor
        for trial in range(25):
            num1 = random.randint(0,sys.maxsize)
            num2 = random.randint(0,sys.maxsize)
            xnum = num1^num2
            hexnumx = '%x'%xnum
            if len(hexnumx)%2:
                hexnumx = '0'+hexnumx
            hexnum1 = '%x'%num1
            if len(hexnum1)%2:
                hexnum1 = '0'+hexnum1
            hexnum2 = '%x'%num2
            if len(hexnum2)%2:
                hexnum2 = '0'+hexnum2
            bytenumx = bytes.fromhex(hexnumx)
            bytenum1 = bytes.fromhex(hexnum1)
            bytenum2 = bytes.fromhex(hexnum2)
            self.assertEqual(byte_xor(bytenum1, bytenum2), bytenumx)

    def test_int_byte_conversion(self):
        from agutil import intToBytes, bytesToInt
        for trial in range(25):
            num = random.randint(0, sys.maxsize)
            self.assertEqual(num, bytesToInt(intToBytes(num)))
        for trial in range(25):
            bytelen = random.randint(16,5000)
            bytestring = os.urandom(bytelen)
            converted = intToBytes(bytesToInt(bytestring), bytelen)
            if bytelen <= 2048:
                self.assertEqual(bytestring, converted)
            else:
                self.assertEqual(len(converted), bytelen)
                self.assertEqual(hash(converted), hash(bytestring))
