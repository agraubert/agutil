import unittest
import os
from py_compile import compile
import sys
import tempfile
from filecmp import cmp

def tempname():
    (handle, name) = tempfile.mkstemp()
    os.close(handle)
    return name

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
        sys.path.append(os.path.dirname(os.path.dirname(cls.script_path)))

    def test_compilation(self):
        compiled_path = compile(self.script_path)
        self.assertTrue(compiled_path)

    # @unittest.skipIf(sys.platform.startswith("win"), "Tempfile doesn't work in this manner on windows")
    def test_manipulation(self):
        import agutil.bio.tsvmanip
        output_file = tempname()
        agutil.bio.tsvmanip.main([
            os.path.join(
                self.data_path,
                'input.txt'
            ),
            output_file,
            '-c',
            '0',
            '-c',
            '4',
            '-d',
            '4::',
            '-d',
            '4:-',
            '--i0',
            '2',
            '-s',
            '2',
            '-s',
            '3',
            '-m',
            '0:3'
        ])
        self.assertTrue(cmp(
            output_file,
            os.path.join(
                self.data_path,
                'output.txt'
            )
        ))
        os.remove(output_file)
