import unittest
import os
from py_compile import compile
import sys
import random

def set_range(bits, start, stop, on=True):
    for i in range(start, stop):
        bits[i] = 1 if on else 0
    return [bit for bit in bits]

def collapse(bits):
    return int(''.join(str(bit) for bit in reversed(bits)),2)

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
            "search_range.py"
        )
        sys.path.append(os.path.dirname(cls.script_path))

    def test_compilation(self):
        compiled_path = compile(self.script_path)
        self.assertTrue(compiled_path)

    def test_core_functions(self):
        import agutil.search_range as sr
        a = sr.search_range()
        self.assertFalse(a.data)
        a.add_range(10,20)
        self.assertEqual(a.data, 0b11111111110000000000)
        self.assertEqual(a.range_count(), 10)
        a.add_range(20,25)
        self.assertEqual(a.data, 0b1111111111111110000000000)
        self.assertEqual(a.range_count(), 15)
        a.remove_range(15,23)
        self.assertEqual(a.data, 0b1100000000111110000000000)
        self.assertEqual(a.range_count(), 7)
        self.assertTrue(a.check(13))
        b = sr.search_range(10,20)
        self.assertEqual(b.data, 0b1111111111)
        self.assertEqual(b.range_count(), 10)

    def test_add_remove_random(self):
        import agutil.search_range as sr
        for trial in range(100):
            a = sr.search_range()
            control = [0]*1000
            c_start = 0
            add = bool(trial%2)
            if trial % 5 == 0:
                start = random.randint(0,1000)
                stop = random.randint(start, 1000)
                a = sr.search_range(start, stop)
                control = set_range(control, start, stop)
                c_start = start

            for manipulation in range(250):
                start = random.randint(0,1000)
                stop = random.randint(start, 1000)
                if start < c_start and add:
                    c_start = start
                if add:
                    a.add_range(start, stop)
                else:
                    a.remove_range(start, stop)
                control = set_range(control, start, stop, add)
                self.assertEqual(a.offset, c_start)
                self.assertEqual(a.data, collapse(control[c_start:]))
                i = len(control)-1
                while i >=0:
                    self.assertEqual(a.check(i), bool(control[i]))
                    i-=random.randint(5,500)
                if collapse(control):
                    self.assertTrue(a.check_range(0,1000))
                for i in a:
                    self.assertTrue(control[i])
                self.assertEqual(a.range_count(), sum(control))
                add = not add

    def test_operators_random(self):
        import agutil.search_range as sr
        for trial in range(100):
            a = sr.search_range()
            b = sr.search_range()
            control_a = [0]*1000
            control_b = [0]*1000
            c_start = 0

            add_a = bool(trial%2)

            if trial%5==0:
                start_a = random.randint(0,1000)
                stop_a = random.randint(start_a, 1000)
                a = sr.search_range(start_a, stop_a)
                start_b = random.randint(0,1000)
                stop_b = random.randint(start_b, 1000)
                b = sr.search_range(start_b, stop_b)
                control_a = set_range(control_a, start_a, stop_a)
                control_b = set_range(control_b, start_b, stop_b)
                c_start = min(start_a, start_b)

            for manipulation in range(250):
                add_b = random.random()<.5
                start_a = random.randint(0,1000)
                start_b = random.randint(0,1000)
                stop_a = random.randint(start_a,1000)
                stop_b = random.randint(start_b,1000)

                if start_a < c_start and add_a:
                    c_start = start_a

                if start_b < c_start and add_b:
                    c_start = start_b

                if add_a:
                    a.add_range(start_a,stop_a)
                else:
                    a.remove_range(start_a,stop_a)

                if add_b:
                    b.add_range(start_b, stop_b)
                else:
                    b.remove_range(start_b, stop_b)

                control_a = set_range(control_a, start_a, stop_a, add_a)
                control_b = set_range(control_b, start_b, stop_b, add_b)

                self.assertEqual((a-b).offset, min(a.offset, b.offset))
                self.assertEqual(min(a.offset, b.offset), c_start)

                self.assertEqual((a-b).data, collapse(control_a[c_start:])&(~collapse(control_b[c_start:])))
                self.assertEqual((a+b).data, collapse(control_a[c_start:])|collapse(control_b[c_start:]))
                self.assertEqual((a&b).data, collapse(control_a[c_start:])&collapse(control_b[c_start:]))

                if manipulation%3 ==0:
                    self.assertEqual((a-b).range_count(), sum(1 for i in range(c_start,1000) if control_a[i]&int(not control_b[i])))
                elif manipulation%3 == 1:
                    self.assertEqual((a+b).range_count(), sum(1 for i in range(c_start,1000) if control_a[i]|control_b[i]))
                else:
                    self.assertEqual((a&b).range_count(), sum(1 for i in range(c_start,1000) if control_a[i]&control_b[i]))

                add_a = not add_a

    def test_ranges_random(self):
        import agutil.search_range as sr
        for trial in range(100):
            a = sr.search_range()
            control = [0]*1000
            c_start = 0
            add = bool(trial%2)
            if trial % 5 == 0:
                start = random.randint(0,1000)
                stop = random.randint(start, 1000)
                a = sr.search_range(start, stop)
                control = set_range(control, start, stop)
                c_start = start

            for manipulation in range(250):
                start = random.randint(0,1000)
                stop = random.randint(start, 1000)
                if start < c_start and add:
                    c_start = start
                if add:
                    a.add_range(start, stop)
                else:
                    a.remove_range(start, stop)
                control = set_range(control, start, stop, add)

                last = 0
                indecies=[]
                for i in range(c_start, 1000):
                    if control[i]!=last:
                        indecies.append(i)
                        last = control[i]

                if last:
                    indecies.append(1000)

                self.assertFalse(len(indecies)%2)
                control_ranges = ([indecies[i], indecies[i+1]] for i in range(0, len(indecies), 2))

                for pair in zip(a.gen_ranges(), control_ranges):
                    self.assertEqual(pair[0][0], pair[1][0])
                    self.assertEqual(pair[0][1], pair[1][1])

                add = not add
