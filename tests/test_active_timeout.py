import unittest
import os
from py_compile import compile
import sys
import random
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
            "src",
            "active_timeout.py"
        )
        sys.path.append(os.path.dirname(os.path.dirname(cls.script_path)))
        random.seed()

    def test_compilation(self):
        compiled_path = compile(self.script_path)
        self.assertTrue(compiled_path)

    def test_time(self):
        from agutil import ActiveTimeout
        with ActiveTimeout(5) as timeout:
            self.assertLessEqual(timeout.socket_timeout, 5.05)
            time.sleep(2)
            self.assertLessEqual(timeout.socket_timeout, 3.05)
            self.assertGreaterEqual(timeout.thread_timeout, timeout.socket_timeout)

    def test_timeout_formats(self):
        from agutil import ActiveTimeout
        with ActiveTimeout(None) as timeout:
            self.assertIsNone(timeout.socket_timeout)
            self.assertEqual(timeout.thread_timeout, -1)

    def test_timeouts(self):
        from agutil import ActiveTimeout, TimeoutExceeded
        with ActiveTimeout(1) as timeout:
            time.sleep(1.05)
            with self.assertRaises(TimeoutExceeded):
                timeout.update()
