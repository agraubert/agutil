import unittest
import os
from py_compile import compile
import sys
import random
import tempfile


def make_random_filename(directory, ext=None):
    name = os.path.join(
        directory.name,
        "".join(chr(random.randint(97,122)) for i in range(25))
        + make_random_exts(ext)
    )
    with open(name, 'w') as w:
        pass
    return name

def make_random_exts(ext):
    pass

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
            "args.py",
        )
        sys.path.append(os.path.dirname(os.path.dirname(cls.script_path)))
        random.seed()

    def test_compilation(self):
        compiled_path = compile(self.script_path)
        self.assertTrue(compiled_path)

    def test_exts(self):
        test_dir = tempfile.TemporaryDirectory()

    def test_dirs(self):
        pass

    def test_fofn(self):
        pass
