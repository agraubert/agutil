import argparse
import os
import re


def fofn(filetype, optional=True):
    if not os.path.isfile(arg):
        raise argparse.ArgumentTypeError("No such file: "+arg)
    if optional:
        try:
            return [filetype(arg)]
        except argparse.ArgumentTypeError as e:
            pass
    with open(arg) as reader:
        return [filetype(line.strip()) for line in reader]


def dirtype(arg):
    if os.path.isfile(arg):
        raise argparse.ArgumentTypeError(arg+" is a file")
    try:
        os.makedirs(arg)
    finally:
        if not os.path.isdir(arg):
            raise argparse.ArgumentTypeError(
                "Unable to create directory: "+arg
            )
        return os.path.abspath(arg)


def filetype(*exts, compression=None):
    def checker(arg):
        if os.path.isfile(arg):
            exts = [
                ext[1:].replace('.', r'\.')
                if ext.startswith('.') else ext.replace('.', r'\.')
                for ext in exts
            ]
            if compression:
                compression = [
                    ext[1:].replace('.', r'\.')
                    if ext.startswith('.') else ext.replace('.', r'\.')
                    for ext in compression
                ]
            pattern = re.compile(
                r'\.(%s)%s$' % (
                    '|'.join(exts),
                    r'\.(%s)*' % '|'.join(compression)
                    if compression is not None else r''
                )
            )
            if pattern.match(arg):
                return os.path.abspath(arg)
            raise argparse.ArgumentTypeError("Invalid file type: %s (%s)" % (
                arg,
                extensions[-1]
            ))
        raise argparse.ArgumentTypeError("No such file: "+arg)
    return checker
