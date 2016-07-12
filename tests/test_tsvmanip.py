import unittest
import os
from py_compile import compile
import sys
import tempfile
from subprocess import call
from filecmp import cmp

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
            "bio",
            "tsvmanip.py"
        )
        cls.data_path = os.path.join(
            os.path.dirname(os.path.abspath(__file__)),
            'data',
            'tsvmanip'
        )

    def test_compilation(self):
        compiled_path = compile(self.script_path)
        self.assertTrue(compiled_path)

    @unittest.skipIf(sys.platform.startswith("win"), "Tempfile doesn't work in this manner on windows")
    def test_manipulation(self):
        output_file = tempfile.NamedTemporaryFile()
        cmd = '%s %s %s %s -c 0 -c 4 -d 4:: -d 4:- --i0 2 -s 2 -s 3 -m 0:3' % (
            sys.executable,
            self.script_path,
            os.path.join(
                self.data_path,
                'input.txt'
            ),
            output_file.name
        )
        self.assertFalse(call([cmd], shell=True))
        self.assertTrue(cmp(
            output_file.name,
            os.path.join(
                self.data_path,
                'output.txt'
            )
        ))
