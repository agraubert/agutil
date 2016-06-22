import unittest
import os
from py_compile import compile
import random
import sys

class test(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        random.seed()
        cls.script_path = os.path.join(
            os.path.dirname(
                os.path.dirname(
                    os.path.abspath(__file__)
                )
            ),
            "agutil",
            "status_bar.py"
        )
        sys.path.append(os.path.dirname(cls.script_path))

    def test_compilation(self):
        compiled_path = compile(self.script_path)
        self.assertTrue(compiled_path)

    def test_rolling(self):
        from agutil.status_bar import status_bar
        q = status_bar(10000, True, debugging=True)
        self.assertEqual(q.display, '['+(' '*q.cols)+'] 0.000%')
        threshold = 10000/q.cols
        self.assertEqual(q.threshold, threshold)
        self.assertEqual(q.update_threshold, .05 * threshold)
        for i in range(10000):
            q.update(i)
            num = int(i*q.cols/10000.0)
            self.assertEqual(q.progress, num)
            self.assertEqual(q.display[0], '[')
            for j in range(q.cols):
                self.assertEqual(q.display[j+1], '=' if j < num else ' ')
            self.assertEqual(q.display[0], '[')
            self.assertLessEqual(abs(float(q.display.split()[-1].strip('% '))- (100*i/10000)), q.update_threshold)
        for i in range(10000, 0, -1):
            q.update(i)
            num = int(i*q.cols/10000.0)
            self.assertEqual(q.progress, num)
            self.assertEqual(q.display[0], '[')
            for j in range(q.cols):
                self.assertEqual(q.display[j+1], '=' if j < num else ' ')
            self.assertEqual(q.display[0], '[')
            self.assertLessEqual(abs(float(q.display.split()[-1].strip('% '))- (100*i/10000)), q.update_threshold)
