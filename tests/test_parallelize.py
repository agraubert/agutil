import unittest
import os
from py_compile import compile
import sys
import random
import subprocess
import threading
import time

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
            "parallel",
            "src",
            "parallelize.py"
        )
        sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(cls.script_path))))
        random.seed()

    def test_compilation(self):
        compiled_path = compile(self.script_path)
        self.assertTrue(compiled_path)

    def test_parallelize(self):
        from agutil.parallel import parallelize as par

        @par(14)
        def test(n):
            time.sleep(random.random() * 5)
            return n

        for x,y in zip(test(range(100)), range(100)):
            self.assertEqual(x,y)

    def test_parallelize2(self):
        from agutil.parallel import parallelize2 as par2

        @par2(17)
        def test(n):
            time.sleep(random.random() * 5)
            return n

        for x,y in [(test(i),i) for i in range(100)]:
            self.assertEqual(x(),y)
