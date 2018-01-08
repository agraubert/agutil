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
            "worker.py"
        )
        sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(cls.script_path))))
        random.seed()

    def test_compilation(self):
        compiled_path = compile(self.script_path)
        self.assertTrue(compiled_path)

    def test_threads(self):
        from agutil.parallel import ThreadWorker

        def test(n):
            time.sleep(random.random() * 5)
            return n

        worker = ThreadWorker(15)

        for x,y in [(worker.dispatch(test,i),i) for i in range(100)]:
            self.assertEqual(x(),y)

        worker.close()

    def test_processes(self):
        from agutil.parallel import ProcessWorker

        def test(n):
            time.sleep(random.random() * 5)
            return n

        worker = ProcessWorker(15)

        for x,y in [(worker.dispatch(test,i),i) for i in range(100)]:
            self.assertEqual(x(),y)

        worker.close()

    def test_exceptions(self):
        from agutil.parallel import ThreadWorker, ProcessWorker

        def test(i):
            time.sleep(random.random() * 5)
            raise SystemExit()

        tworker = ThreadWorker(1)
        pworker = ProcessWorker(1)

        with self.assertRaises(SystemExit):
            tworker.dispatch(test,1)()

        with self.assertRaises(SystemExit):
            pworker.dispatch(test,1)()

        tworker.close()
        pworker.close()
