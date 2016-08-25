import unittest
import os
from py_compile import compile
import random
import sys
import tempfile
from filecmp import cmp
import csv

def tempname():
    (handle, name) = tempfile.mkstemp()
    os.close(handle)
    return name

class test(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        sys.stdout = open(os.devnull, mode='w')
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

    @classmethod
    def tearDownClass(cls):
        sys.stdout.close()
        sys.stdout = sys.__stdout__

    def test_compilation(self):
        compiled_path = compile(self.script_path)
        self.assertTrue(compiled_path)

    # @unittest.skipIf(sys.platform.startswith("win"), "Tempfile doesn't work in this manner on windows")
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
            ),
            '-v'
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
        raw_reader = open(os.path.join(
            self.data_path,
            'output_wSilents.bed.key'
        ), mode='r')
        reader = csv.DictReader(raw_reader, delimiter='\t')
        intake = [entry for entry in reader if random.random() <= .1]
        raw_reader.close()
        cmd = ['lookup', os.path.join(
            output_dir.name,
            'output.bed.key'
        ), '--suppress']
        for line in intake:
            cmd.append(line['Key'])
        result = agutil.bio.maf2bed.main(cmd)
        self.assertEqual(len(result), len(intake))
        intake.sort(key=lambda entry:entry['Key'])
        result.sort(key=lambda entry:entry['Key'])
        for i in range(len(intake)):
            for key in intake[i]:
                self.assertTrue(key in result[i])
                self.assertEqual(intake[i][key], result[i][key])
        output_dir.cleanup()

    # @unittest.skipIf(sys.platform.startswith("win"), "Tempfile doesn't work in this manner on windows")
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
            '--exclude-silent',
            '-v'
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
        raw_reader = open(os.path.join(
            self.data_path,
            'output_noSilents.bed.key'
        ), mode='r')
        reader = csv.DictReader(raw_reader, delimiter='\t')
        intake = [entry for entry in reader if random.random() <= .1]
        raw_reader.close()
        cmd = ['lookup', os.path.join(
            output_dir.name,
            'output.bed.key'
        ), '--suppress']
        for line in intake:
            cmd.append(line['Key'])
        result = agutil.bio.maf2bed.main(cmd)
        self.assertEqual(len(result), len(intake))
        intake.sort(key=lambda entry:entry['Key'])
        result.sort(key=lambda entry:entry['Key'])
        for i in range(len(intake)):
            for key in intake[i]:
                self.assertTrue(key in result[i])
                self.assertEqual(intake[i][key], result[i][key])
        output_dir.cleanup()

    # @unittest.skipIf(sys.platform.startswith("win"), "Tempfile doesn't work in this manner on windows")
    def test_output_noKeyfile(self):
        import agutil.bio.maf2bed
        output_file = tempname()
        agutil.bio.maf2bed.main([
            'convert',
            os.path.join(
                self.data_path,
                'source.txt'
            ),
            output_file,
            '--skip-keyfile',
            '-v'
        ])
        self.assertTrue(cmp(
            output_file,
            os.path.join(
                self.data_path,
                'output_wSilents_noKey.bed'
            )
        ))
        os.remove(output_file)

    # @unittest.skipIf(sys.platform.startswith("win"), "Tempfile doesn't work in this manner on windows")
    def test_output_noSilents_noKeyfile(self):
        import agutil.bio.maf2bed
        output_file = tempname()
        agutil.bio.maf2bed.main([
            'convert',
            os.path.join(
                self.data_path,
                'source.txt'
            ),
            output_file,
            '--exclude-silent',
            '--skip-keyfile',
            '-v'
        ])
        self.assertTrue(cmp(
            output_file,
            os.path.join(
                self.data_path,
                'output_noSilents_noKey.bed'
            )
        ))
        os.remove(output_file)
