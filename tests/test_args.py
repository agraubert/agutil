import unittest
import os
from py_compile import compile
import sys
import random
import tempfile
import contextlib
import shutil
from argparse import ArgumentTypeError as argError

def make_random_filename(directory, ext=None):
    name = os.path.join(
        directory,
        os.urandom(8).hex()
        + '.' + make_random_exts(ext)
    )
    with open(name, 'w') as w:
        return name

def make_random_exts(ext):
    if ext is None:
        ext = os.urandom(1).hex()
    return ext

def make_fofn(directory, *files):
    path = make_random_filename(directory, 'fofn')
    with open(path, 'w') as w:
        w.write('\n'.join(files))
    return path

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
            "args.py",
        )
        sys.path.append(os.path.dirname(os.path.dirname(cls.script_path)))
        random.seed()

    def test_compilation(self):
        compiled_path = compile(self.script_path)
        self.assertTrue(compiled_path)

    def test_files(self):
        from agutil import FileType
        with tempfile.TemporaryDirectory() as workspace:
            for trial in range(5):
                exts = [
                    make_random_exts(None)
                    for i in range(random.randint(1, 10))
                ]
                checker = FileType(*exts)
                compression = FileType(*exts, compression=True)
                with self.assertRaises(argError):
                    checker('not-a-real-file')
                with self.assertRaises(argError):
                    checker(__file__)
                with self.assertRaises(argError):
                    checker(make_random_filename(workspace, os.urandom(2).hex()))
                for ext in exts:
                    goodfile = os.path.abspath(make_random_filename(workspace, ext))
                    gzfile = os.path.abspath(make_random_filename(workspace, ext+'.gz'))
                    bzfile = os.path.abspath(make_random_filename(workspace, ext+'.bz2'))
                    self.assertEqual(
                        goodfile,
                        checker(goodfile)
                    )
                    self.assertEqual(
                        gzfile,
                        compression(gzfile)
                    )
                    self.assertEqual(
                        bzfile,
                        compression(bzfile)
                    )
                    with self.assertRaises(argError):
                        checker(bzfile)

    def test_dirs(self):
        from agutil import DirType
        checker = DirType()
        for trial in range(5):
            with tempfile.TemporaryDirectory() as workspace:
                self.assertEqual(
                    os.path.abspath(workspace),
                    checker(workspace)
                )
                with self.assertRaises(argError):
                    checker(make_random_filename(workspace))

    def test_fofns(self):
        from agutil import FOFNType
        with tempfile.TemporaryDirectory() as workspace:
            for trial in range(5):
                exts = [
                    make_random_exts(None)
                    for i in range(random.randint(1, 10))
                ]
                checker = FOFNType(*exts)
                empty_list_checker = FOFNType(*exts, min_paths=0, as_list=True)
                handle_checker = FOFNType(*exts, as_handle=True)
                handle_list_checker = FOFNType(*exts, as_list=True, as_handle=True)
                direct_checker = FOFNType(*exts, allow_direct=True)
                direct_list_checker = FOFNType(*exts, as_list=True, allow_direct=True)
                direct_handle_checker = FOFNType(*exts, as_handle=True, allow_direct=True)
                with self.assertRaises(argError):
                    checker('not-a-real-file')
                with self.assertRaises(argError):
                    checker(__file__)
                empty_fofn = make_fofn(workspace)
                with self.assertRaises(argError):
                    checker(empty_fofn)
                with self.assertRaises(argError):
                    checker(make_fofn(workspace, 'not-a-real-file'))
                with self.assertRaises(argError):
                    checker(make_fofn(workspace, make_random_filename(workspace)))
                self.assertIsInstance(empty_list_checker(empty_fofn), list)
                self.assertListEqual(empty_list_checker(empty_fofn), [])
                acceptable = [make_random_filename(workspace, ext) for ext in exts]
                good_fofn = make_fofn(workspace, *acceptable)
                self.assertListEqual(
                    empty_list_checker(good_fofn),
                    acceptable
                )
                with contextlib.closing(handle_checker(good_fofn)) as handle:
                    self.assertEqual(
                        os.path.abspath(handle.name),
                        os.path.abspath(good_fofn)
                    )
                handles = handle_list_checker(good_fofn)
                self.assertEqual(len(acceptable), len(handles))
                for path, handle in zip(acceptable, handles):
                    self.assertEqual(
                        os.path.abspath(path),
                        os.path.abspath(handle.name)
                    )
                    handle.close()
                with self.assertRaises(argError):
                    checker(acceptable[0])
                tmp_path = direct_checker(acceptable[0])
                with open(tmp_path) as r:
                    self.assertEqual(
                        acceptable[0],
                        r.read().strip()
                    )
                self.assertListEqual(
                    direct_list_checker(acceptable[0]),
                    [acceptable[0]]
                )
                self.assertEqual(
                    direct_handle_checker(acceptable[0]).read().strip(),
                    acceptable[0]
                )


    def test_fofns_all_types(self):
        from agutil import FOFNType, DirType, FileType
        with tempfile.TemporaryDirectory() as workspace:
            for trial in range(5):
                exts = [
                    make_random_exts(None)
                    for i in range(random.randint(1, 10))
                ]
                checker = FOFNType(*exts, as_list=True, allow_direct=True)
                all_checker = FOFNType(DirType(), FileType(*exts, compression=True), as_list=True, allow_direct=True)
                acceptable = [make_random_filename(workspace, ext) for ext in exts]
                acceptable_fofn = make_fofn(workspace, *acceptable)
                _dir = os.path.join(workspace, 'dir-'+os.urandom(8).hex())
                os.mkdir(_dir)
                with_dirs = acceptable + [_dir] + [
                    make_random_filename(workspace, ext+'.gz') for ext in exts
                ]
                with_dirs_fofn = make_fofn(workspace, *with_dirs)
                self.assertListEqual(
                    checker(acceptable_fofn),
                    acceptable
                )
                self.assertListEqual(
                    checker(acceptable[0]),
                    [acceptable[0]]
                )
                self.assertListEqual(
                    checker(acceptable_fofn),
                    all_checker(acceptable_fofn)
                )
                self.assertListEqual(
                    checker(acceptable[0]),
                    all_checker(acceptable[0])
                )
                with self.assertRaises(argError):
                    checker(with_dirs_fofn)
                self.assertListEqual(
                    all_checker(with_dirs_fofn),
                    with_dirs
                )
