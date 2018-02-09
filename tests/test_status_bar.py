import unittest
import os
from py_compile import compile
import random
import sys

class test(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        # sys.stdout = open(os.devnull, 'w')
        random.seed()
        cls.script_path = os.path.join(
            os.path.dirname(
                os.path.dirname(
                    os.path.abspath(__file__)
                )
            ),
            "agutil",
            "src",
            "status_bar.py"
        )
        sys.path.append(os.path.dirname(os.path.dirname(cls.script_path)))

    # @classmethod
    # def tearDownClass(cls):
    #     sys.stdout.close()
    #     sys.stdout = sys.__stdout__

    def test_compilation(self):
        compiled_path = compile(self.script_path)
        self.assertTrue(compiled_path)

    def test_rolling(self):
        from agutil import status_bar
        with status_bar(10000, True, debugging=True) as q:
            self.assertEqual(q.display, '['+(' '*q.cols)+'] 0.000%')
            q.prepend("PRE ")
            self.assertEqual(q.display, 'PRE ['+(' '*q.cols)+'] 0.000%')
            q.append(" POST")
            self.assertEqual(q.display, 'PRE ['+(' '*q.cols)+'] 0.000% POST')
            threshold = 10000/q.cols
            self.assertEqual(q.threshold, threshold)
            self.assertEqual(q.update_threshold, .00005 * 10000)
            for i in range(10000):
                q.update(i)
                num = int(i*q.cols/10000.0)
                self.assertEqual(q.progress, num)
                self.assertEqual(q.display[:5], 'PRE [')
                for j in range(q.cols):
                    self.assertEqual(q.display[j+5], '=' if j < num else ' ')
                self.assertEqual(q.display[q.cols+5], ']')
                self.assertEqual(q.display[-5:], ' POST')
                self.assertLessEqual(abs(float(q.display.split()[-2].strip('% '))- (100*i/10000)), q.update_threshold)
            for i in range(10000, 0, -1):
                q.update(i)
                num = int(i*q.cols/10000.0)
                self.assertEqual(q.progress, num)
                self.assertEqual(q.display[:5], 'PRE [')
                for j in range(q.cols):
                    self.assertEqual(q.display[j+5], '=' if j < num else ' ')
                self.assertEqual(q.display[q.cols+5], ']')
                self.assertEqual(q.display[-5:], ' POST')
                self.assertLessEqual(abs(float(q.display.split()[-2].strip('% '))- (100*i/10000)), q.update_threshold)
        self.assertEqual(q.display, ' '*len(q.display))
        q.update(0)

    def test_iter(self):
        from agutil import status_bar
        bar = None
        first = True
        for i in status_bar.iter(range(0,1000), iter_debug=True, debugging=True):
            if first:
                self.assertIsInstance(i, status_bar)
                bar = i
                first = False
                continue
            self.assertIsInstance(i,int)
            self.assertEqual(bar.current, i)
            self.assertEqual(bar.progress, int(i*bar.cols/1000.0))
