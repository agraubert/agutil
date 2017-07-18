import unittest
import os
from py_compile import compile
import sys
import random
import subprocess

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
            "shell.py"
        )
        sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(cls.script_path))))
        random.seed()

    def test_compilation(self):
        compiled_path = compile(self.script_path)
        self.assertTrue(compiled_path)

    def test_shell_commands(self):
        from agutil import cmd
        commands = [
            'ls',
            'pwd',
            'echo hi',
            'ps -o command'
        ]
        for command in commands:
            expected = subprocess.check_output(
                command,
                shell=True,
            )
            observed = cmd(command, display=False)
            self.assertEqual(expected, observed.rawbuffer)
