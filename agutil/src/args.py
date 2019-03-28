import argparse
import os
import re
import gzip
import bz2
from atexit import register
from itertools import islice
from io import StringIO
from tempfile import mkstemp


class ArgType(object):
    pass


class FileType(ArgType):
    def __init__(
        self,
        *extensions,
        compression=False,
        output=None,
        existence=os.path.isfile,
        **kwargs
    ):
        """
        Create a new FileType checker.
        Provide a list of valid extensions for the file.
        If no extensions are provided, just ensire the file is a valid filepath
        If compression is False (default), require path to end in one of the
        given extensions. If compression is True, require path to end in one of
        the given extensions, or an extension followed by [.gz, .bgz, or .bz2]
        If compression is a list, use that list as the set of acceptable
        compression extensions. If output is None (default), the checker will
        return absolute paths when called. If output is any string, the checker
        will open the file using the provided string as the flags to open(),
        and return the file object when called. If output is a string,
        compression is True, and the file ends in one of the allowed
        compression extensions, the checker will return a file-like object
        opened with the provied string using one of the standard library
        compression modules so that the object will return decomressed data.
        Any additional keyword arguments passed to this constructor will be
        passed to the open function (if output is not None)
        """
        self.extensions = [
            ext[1:] if ext.startswith('.') else ext
            for ext in extensions
        ] if len(extensions) else [r'.+']
        self.compression = (
            ['gz', 'bgz', 'bz2'] if compression is True else [
                ext[1:] if ext.startswith('.') else ext
                for ext in compression
            ]

        ) if compression is not False else None
        pattern = r'.+\.(?:{})'.format('|'.join(self.extensions))
        if self.compression is not None:
            pattern += r'(\.(?:{}))?'.format('|'.join(self.compression))
        self.pattern = re.compile(pattern + r'$')
        self.output = output
        self.existence = existence
        self.kwargs = {k: v for k, v in kwargs.items()}

    def __call__(self, arg):
        """
        Validates an argument.
        Ensures that the argument is a valid filepath.
        Raises an ArgumentTypeError if that is not true.
        Returns either an absolute filepath or a file-like object, as
        determined by arguments to __init__
        """
        if not self.existence(arg):
            raise argparse.ArgumentTypeError("No such file: "+arg)
        match = self.pattern.match(os.path.basename(arg))
        if not match:
            raise argparse.ArgumentTypeError(
                arg+" is not an acceptable filetype ({})".format(
                    self.extensions
                )
            )
        if isinstance(self.output, str):
            if match.group(1) in {'.gz', '.bgz'}:
                return gzip.open(
                    arg,
                    self.output,
                    **self.kwargs
                )
            elif match.group(1) == '.bz2':
                return bz2.open(
                    arg,
                    self.output,
                    **self.kwargs
                )
            return open(
                arg,
                self.output,
                **self.kwargs
            )
        return os.path.abspath(arg) if os.path.isfile(arg) else arg


class DirType(ArgType):
    def __init__(self, existence=os.path.isdir):
        self.existence = existence

    def __call__(self, arg):
        if not self.existence(arg):
            raise argparse.ArgumentTypeError("No such directory: "+arg)
        return os.path.abspath(arg) if os.path.isdir(arg) else arg


class FOFNType(ArgType):
    def __init__(
        self,
        *extensions,
        min_paths=1,
        as_list=False,
        as_handle=False,
        allow_direct=False,
        existence=os.path.isfile,
        **kwargs
    ):
        """
        Return a checker expecting a File Of File Names (FOFN).
        Checker expects file to exist and for each line to contain a filepath.
        Extensions should be a list of file extensions or File/Dir/FOFNType
        objects that are allowed in the FOFN.

        min_paths specifies the minimum required files to appear in the FOFN.
        The first min_paths lines of the file will be checked to contain valid
        filepaths meeting one of the provided extensions.
        If as_list is True, the min_paths argument is ignored.
        If as_list is False, and min_paths is less than 1, the file contents
        will not be checked.

        as_list specifies whether the checker should return a list of filepaths
        contained in the FOFN, or just the filepath to the FOFN itself.
        If as_list is True, each line will be read from the file and checked
        against the provided extensions.

        as_handle specifies whether the checker should open and return a file-
        like object to the FOFN.
        If as_handle is True, the checker will open the file. If as_list is
        also True, the checker will return a list of file-like objects for each
        file specified in the FOFN.

        allow_direct specifies whether or not the checker is allowed to check
        the provided FOFN is actually just a path with one of the allowed
        extensions. If allow_direct is True, and the file failed the above
        tests, fallback on checking if the provided file ends with one of the
        allowed extensions. If so, the checker procedes as if it had a FOFN
        just containing the provided filepath

        Any keyword arguments provided to this constructor will also be
        provided to the open function of any file-like object(s) returned by
        the checker
        """
        self.checkers = [
            ext for ext in extensions if isinstance(ext, ArgType)
        ]
        self.checkers.append(FileType(*[
            ext for ext in extensions if not isinstance(ext, ArgType)
        ]))
        self.min_paths = min_paths
        self.as_list = as_list
        self.as_handle = as_handle
        self.allow_direct = allow_direct
        self.existence = existence
        self.kwargs = {k: v for k, v in kwargs.items()}

    def check_path(self, path):
        """
        Checks that the provided path ends with a valid extension.
        Used to check the filepaths within a FOFN.
        To check if a path is a FOFN containing valid paths, call the checker
        on the filepath
        """
        for checker in self.checkers:
            try:
                return checker(path)
            except argparse.ArgumentTypeError:
                pass
        raise argparse.ArgumentTypeError(path+" is not an acceptable filetype")

    def _list(self, paths):
        # Return either a list of paths or a list of path handles
        if self.as_handle:
            return [
                open(path, **self.kwargs) for path in paths
            ]
        return paths

    def _path(self, path, direct=False):
        # Return either the path or a handle
        # if direct is true and as_handle is false, make a file
        if direct:
            if self.as_handle:
                return StringIO(path)
            handle, filepath = mkstemp()
            os.write(handle, path.encode())
            os.close(handle)

            @register
            def _cleanup():
                if os.path.exists(filepath):
                    os.remove(filepath)

            return filepath
        if self.as_handle:
            return open(path, **self.kwargs)
        return os.path.abspath(path) if os.path.isfile(path) else path

    def __call__(self, arg):
        """
        Validates an argument.
        Ensures that the argument is a valid filepath and is a FOFN containing
        valid filepaths.
        Raises an ArgumentTypeError if either of those are not true.
        Return type determined by arguments to constructor. Returns either a
        single object or a list of objects (determined by as_list). Object will
        either be a filepath or a file handle (determined by as_handle)
        """
        if not self.existence(arg):
            raise argparse.ArgumentTypeError("No such file: "+arg)
        try:
            if self.as_list or self.min_paths >= 1:
                with open(arg) as r:
                    # Get a reader that will only read min_paths lines
                    reader = r if self.as_list else islice(r, self.min_paths)
                    paths = [
                        self.check_path(line.rstrip()) for line in reader
                    ]
                if len(paths) < self.min_paths:
                    raise argparse.ArgumentTypeError(
                        arg+" did not contain enough files (%d/%d)" % (
                            len(paths),
                            self.min_paths
                        )
                    )
                if self.as_list:
                    return self._list(paths)
            return self._path(arg)
        except argparse.ArgumentTypeError as e:
            if self.allow_direct and self.min_paths <= 1:
                try:
                    path = self.check_path(arg)
                    if self.as_list:
                        return self._list([path])
                    return self._path(path, direct=True)
                except argparse.ArgumentTypeError:
                    raise argparse.ArgumentTypeError(
                        arg+" was not an acceptable file or FOFN"
                    ) from e
            raise
