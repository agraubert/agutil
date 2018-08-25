import unittest
import unittest.mock
import os
from py_compile import compile
import sys
import random
import time
import tempfile
from filecmp import cmp
from .utils import TempDir

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
            "logger.py"
        )
        cls.data_path = os.path.join(
            os.path.dirname(os.path.abspath(__file__)),
            'data',
            'logger'
        )
        sys.path.append(os.path.dirname(os.path.dirname(cls.script_path)))
        random.seed()
        cls.test_dir = TempDir()

    def test_compilation(self):
        compiled_path = compile(self.script_path)
        self.assertTrue(compiled_path)

    def test_basic_logging(self):
        import agutil.src.logger
        time_mock = unittest.mock.Mock(side_effect = lambda fmt, time=0:fmt)
        agutil.src.logger.time.strftime = time_mock
        output_file = self.test_dir()
        log = agutil.src.logger.Logger(output_file, loglevel=agutil.src.logger.Logger.LOGLEVEL_DETAIL)
        log.log("Test message")
        log.log("More messages!", sender="me")
        log.log("OH NO! This one's an error!", "Foo", "ERROR")
        foo_bound = log.bindToSender("Foo")
        log.mute("Foo", "Bar")
        foo_bound("Message 1")
        foo_bound("Message 2")
        log.log("This should appear in the log, but not the dump", "Bar", "WARN")
        foo_bound("Message 3")
        log.unmute("Foo")
        log.log("I've been unmuted!", "Foo")
        log.log("This should be a warning", "Anyone", "BLORG")
        time.sleep(.2)
        log.addChannel("BLORG", 15)
        log.setChannelCollection("BLORG", True)
        log.log("This should be seen", "Anyone", "BLORG")
        log.setChannelCollection("WARN", False)
        log.setChannelCollection("WARN", True)
        time.sleep(.2)
        log.log("This should appear in the dump", "Bar", "WARN")
        time.sleep(.1)
        self.assertFalse(log.close())
        self.assertTrue(cmp(
            output_file,
            os.path.join(
                self.data_path,
                'logger_compare.txt'
            )
        ))
        log.close()
        os.remove(output_file)
