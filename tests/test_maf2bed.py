import unittest
import os
from py_compile import compile
import random
import sys
import tempfile
from subprocess import call
from filecmp import cmp

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
            "bio",
            "maf2bed.py"
        )
        cls.data_path = os.path.join(
            os.path.dirname(os.path.abspath(__file__)),
            'data',
            'maf2bed'
        )

    def test_compilation(self):
        compiled_path = compile(self.script_path)
        self.assertTrue(compiled_path)

    def test_output(self):
        output_dir = tempfile.TemporaryDirectory()
        cmd = '%s %s convert %s %s' % (
            sys.executable,
            self.script_path,
            os.path.join(
                self.data_path,
                'source.txt'
            ),
            os.path.join(
                output_dir.name,
                'output.bed'
            )
        )
        self.assertFalse(call([cmd], shell=True))
        self.assertTrue(cmp(
            os.path.join(
                output_dir.name,
                'output.bed'
            ),
            os.path.join(
                self.data_path,
                'output_wSilents.bed'
            )
        ))
        self.assertTrue(cmp(
            os.path.join(
                output_dir.name,
                'output.bed.key'
            ),
            os.path.join(
                self.data_path,
                'output_wSilents.bed.key'
            )
        ))
        output_dir.cleanup()

    def test_output_noSilents(self):
        output_dir = tempfile.TemporaryDirectory()
        cmd = '%s %s convert %s %s --exclude-silent' % (
            sys.executable,
            self.script_path,
            os.path.join(
                self.data_path,
                'source.txt'
            ),
            os.path.join(
                output_dir.name,
                'output.bed'
            )
        )
        self.assertFalse(call([cmd], shell=True))
        self.assertTrue(cmp(
            os.path.join(
                output_dir.name,
                'output.bed'
            ),
            os.path.join(
                self.data_path,
                'output_noSilents.bed'
            )
        ))
        self.assertTrue(cmp(
            os.path.join(
                output_dir.name,
                'output.bed.key'
            ),
            os.path.join(
                self.data_path,
                'output_noSilents.bed.key'
            )
        ))
        output_dir.cleanup()

    def test_output_noKeyfile(self):
        output_file = tempfile.NamedTemporaryFile()
        cmd = '%s %s convert %s %s --skip-keyfile' % (
            sys.executable,
            self.script_path,
            os.path.join(
                self.data_path,
                'source.txt'
            ),
            output_file.name
        )
        self.assertFalse(call([cmd], shell=True))
        self.assertTrue(cmp(
            output_file.name,
            os.path.join(
                self.data_path,
                'output_wSilents_noKey.bed'
            )
        ))

    def test_output_noSilents_noKeyfile(self):
        output_file = tempfile.NamedTemporaryFile()
        cmd = '%s %s convert %s %s --exclude-silent --skip-keyfile' % (
            sys.executable,
            self.script_path,
            os.path.join(
                self.data_path,
                'source.txt'
            ),
            output_file.name
        )
        self.assertFalse(call([cmd], shell=True))
        self.assertTrue(cmp(
            output_file.name,
            os.path.join(
                self.data_path,
                'output_noSilents_noKey.bed'
            )
        ))
