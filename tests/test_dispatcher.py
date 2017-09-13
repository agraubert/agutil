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
        t0 = time.monotonic()
        for x,y in zip(disp, range(100)):
            self.assertEqual(x,y)
        t1 = time.monotonic()
        for x,y in zip(disp, range(100)):
            self.assertEqual(x,y)
        self.assertLess(time.monotonic()-t1, t1-t0)

    def test_exceptions(self):
        from agutil.parallel import Dispatcher

        def test(i):
            time.sleep(random.random() * 5)
            if i == 7:
                raise SystemExit()
            return i

        with self.assertRaises(SystemExit):
            disp = Dispatcher(
                test,
                i=range(15)
            )
            for x,y in zip(disp, range(15)):
                self.assertEqual(x,y)

        def test2(i):
            time.sleep(random.random() * 5)
            return SystemExit()

        disp = Dispatcher(
            test2,
            range(10)
        )
        for exc in disp:
            self.assertIsInstance(exc, SystemExit)
