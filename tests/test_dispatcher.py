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
            "dispatcher.py"
        )
        sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(cls.script_path))))
        random.seed()

    def test_compilation(self):
        compiled_path = compile(self.script_path)
        self.assertTrue(compiled_path)

    def test_dispatch(self):
        from agutil.parallel import Dispatcher

        def test(i):
            time.sleep(random.random() * 5)
            return i

        disp = Dispatcher(
            test,
            i=range(100)
        )
        for x,y in zip(disp, range(100)):
            self.assertEqual(x,y)

    def test_parallelize(self):
        from agutil.parallel import parallelize

        @parallelize(14)
        def test(n):
            time.sleep(random.random() * 5)
            return n

        for x,y in zip(test(range(100)), range(100)):
            self.assertEqual(x,y)
