import unittest
import os
from py_compile import compile

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
            "tsvmanip.py"
        )

    def test_compilation(self):
        compiled_path = compile(self.script_path)
        self.assertTrue(compiled_path)
