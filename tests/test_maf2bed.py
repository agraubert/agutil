import unittest
import os
from py_compile import compile
import random
import sys
import tempfile
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
        sys.path.append(os.path.dirname(os.path.dirname(cls.script_path)))

    def test_compilation(self):
        compiled_path = compile(self.script_path)
        self.assertTrue(compiled_path)

    @unittest.skipIf(sys.platform.startswith("win"), "Tempfile doesn't work in this manner on windows")
    def test_output(self):
        import agutil.bio.maf2bed
        output_dir = tempfile.TemporaryDirectory()
        agutil.bio.maf2bed.main([
            'convert',
            os.path.join(
                self.data_path,
                'source.txt'
            ),
            os.path.join(
                output_dir.name,
                'output.bed'
            )
        ])
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

    @unittest.skipIf(sys.platform.startswith("win"), "Tempfile doesn't work in this manner on windows")
    def test_output_noSilents(self):
        import agutil.bio.maf2bed
        output_dir = tempfile.TemporaryDirectory()
        agutil.bio.maf2bed.main([
            'convert',
            os.path.join(
                self.data_path,
                'source.txt'
            ),
            os.path.join(
                output_dir.name,
                'output.bed'
            ),
            '--exclude-silent'
        ])
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

    @unittest.skipIf(sys.platform.startswith("win"), "Tempfile doesn't work in this manner on windows")
    def test_output_noKeyfile(self):
        import agutil.bio.maf2bed
        output_file = tempfile.NamedTemporaryFile()
        agutil.bio.maf2bed.main([
            'convert',
            os.path.join(
                self.data_path,
                'source.txt'
            ),
            output_file.name,
            '--skip-keyfile'
        ])
        self.assertTrue(cmp(
            output_file.name,
            os.path.join(
                self.data_path,
                'output_wSilents_noKey.bed'
            )
        ))

    @unittest.skipIf(sys.platform.startswith("win"), "Tempfile doesn't work in this manner on windows")
    def test_output_noSilents_noKeyfile(self):
        import agutil.bio.maf2bed
        output_file = tempfile.NamedTemporaryFile()
        agutil.bio.maf2bed.main([
            'convert',
            os.path.join(
                self.data_path,
                'source.txt'
            ),
            output_file.name,
            '--exclude-silent',
            '--skip-keyfile'
        ])
        self.assertTrue(cmp(
            output_file.name,
            os.path.join(
                self.data_path,
                'output_noSilents_noKey.bed'
            )
        ))
