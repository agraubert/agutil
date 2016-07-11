import unittest
import os
from py_compile import compile
import sys

class test(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.source_dir = os.path.join(
            os.path.dirname(
                os.path.dirname(
                    os.path.abspath(__file__)
                )
            ),
            "agutil",
            "security",
            "src"
        )
        sys.path.append(os.path.dirname(os.path.dirname(cls.source_dir)))

    def test_compilation(self):
        core_path = compile(os.path.join(
            self.source_dir,
            "core.py"
        ))
        channel_path = compile(os.path.join(
            self.source_dir,
            "channel.py"
        ))
        protocols_path = compile(os.path.join(
            self.source_dir,
            "protocols.py"
        ))
        self.assertTrue(core_path, "core.py compilation error")
        self.assertTrue(channel_path, "channel.py compilation error")
        self.assertTrue(protocols_path, "protocols.py compilation error")
