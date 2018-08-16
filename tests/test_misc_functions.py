import unittest
import os
from py_compile import compile
import sys
import hashlib
import random
import tempfile
import threading

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
            num1 = random.randint(0,sys.maxsize**2)
            num2 = random.randint(0,sys.maxsize**2)
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
            if len(bytenumx) < max(len(bytenum1), len(bytenum2)):
                bytenumx = (bytes(max(len(bytenum1), len(bytenum2))-len(bytenumx)))+bytenumx
            self.assertEqual(byte_xor(bytenum1, bytenum2), bytenumx)
            self.assertEqual(byte_xor(bytenum2, bytenum1), bytenumx)

    def test_int_byte_conversion(self):
        from agutil import intToBytes, bytesToInt
        for trial in range(25):
            num = random.randint(0, sys.maxsize**2)
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

    def test_hashfile(self):
        from agutil import hashfile
        temp_dir = tempfile.TemporaryDirectory()
        #Test shake algorithms later
        for algo in hashlib.algorithms_available:
            for trial in range(2):
                filename = os.path.join(
                    temp_dir.name,
                    '%s-trial-%d'%(algo, trial)
                )
                writer = open(filename, mode='w')
                hasher = hashlib.new(algo)
                for line in range(32):
                    content = make_random_string(length=1024)
                    writer.write(content)
                    hasher.update(content.encode())
                writer.close()
                if algo.startswith('shake'):
                    length = int(2**random.randint(4,10))
                    self.assertEqual(hashfile(filename, algo, length), hasher.digest(length))
                else:
                    self.assertEqual(hashfile(filename, algo), hasher.digest())
        temp_dir.cleanup()

    def test_byte_size(self):
        from agutil import byteSize
        from math import log
        import re
        pattern = re.compile(r'(\d+(\.\d)?)([A-Z]i)?B')
        for trial in range(25):
            num = random.randint(0, sys.maxsize)
            formatted = byteSize(num)
            self.assertRegex(formatted, pattern)
            self.assertLess(float(pattern.match(formatted).group(1)), 1024.0)

    def test_first(self):
        from agutil import first
        for trial in range(25):
            data = [random.randint(0,100000) for i in range(1000)]
            target = data[random.randint(0,999)]
            self.assertEqual(target, first(data, target))
            self.assertEqual(target, first(data, lambda x:x==target))

    def test_splicing(self):
        from agutil import splice
        for trial in range(25):
            width = random.randint(1, 100)
            data = [
                [random.random() for c in range(width)]
                for r in range(random.randint(1,10000))
            ]
            column_iters = splice(data)
            self.assertEqual(len(column_iters), width)
            i = 0
            for r in range(len(data)):
                for c in range(width):
                    self.assertEqual(next(column_iters[c]), data[r][c])
                i += 1
            self.assertEqual(i,len(data))

    def test_context_lock(self):
        from agutil import context_lock, LockTimeoutExceeded
        lock = threading.Lock()
        with context_lock(lock) as l:
            # This assertion is mostly to ensure we reach this block
            self.assertEqual(lock, l)
        lock.acquire()
        with self.assertRaises(LockTimeoutExceeded):
            with context_lock(lock, 1):
                self.fail("context_lock somehow managed to acquire")
