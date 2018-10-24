# agutil
* Master build status: [![Master Build Status](https://travis-ci.org/agraubert/agutil.svg?branch=master)](https://travis-ci.org/agraubert/agutil) [![Live Package Version](https://img.shields.io/pypi/v/agutil.svg)](https://pypi.python.org/pypi/agutil)
* Development build status: [![Dev Build Status](https://travis-ci.org/agraubert/agutil.svg?branch=dev)](https://travis-ci.org/agraubert/agutil) [![Dev Coverage Status](https://coveralls.io/repos/github/agraubert/agutil/badge.svg?branch=dev)](https://coveralls.io/github/agraubert/agutil?branch=dev)

A collection of python utilities

__Version:__ 2.1.2

###### Tools:
* search_range (A utility for manipulating numerical ranges)
* status_bar (A simple progress bar indicator)
* Logger (A class for fast, simple, logging)
* Several standalone utility methods (See the [agutil module page](https://github.com/agraubert/agutil/wiki/agutil-%28main-module%29) on the wiki)

The __bio__ package:

* maf2bed (A command line utility for parsing a .maf file and converting coordinates from 1-based (maf standard) to 0-based (bed standard))

The __io__ package:

* Socket (A low-level network IO class built on top of the standard socket class)
* SocketServer (A low-level listen server to accept connections and return Socket classes)
* QueuedSocket (A low-level network IO class built to manage input across multiple channels)

The __parallel__ package:

* Dispatcher (A class for managing background threads for running tasks in parallel)
* parallelize (A decorator to easily convert a regular function into a parallelized version)
* parallelize2 (A similar parallelization decorator with a slightly different flavor)

The __security__ package:

* SecureSocket (A mid-level network IO class built to manage encrypted network communications)
* SecureConnection (A high-level, multithreaded class for sending and receiving encrypted files and messages)
* SecureServer (A low-level listen server to accept connections and return SecureConnection instances)
* encryptFile and decryptFile (Simple methods for encrypting and decrypting local files)
* agutil-secure (A command line utility for encrypting and decrypting files)

## Documentation:
Detailed documentation of these packages can be found on the [agutil Github wiki page](https://github.com/agraubert/agutil/wiki)

## Installation note:
This package requires PyCrypto, which typically has issues compiling on windows.  If you are on windows and `pip install agutil` fails during the installation of PyCrypto, then follow the instructions [here](https://github.com/sfbahr/PyCrypto-Wheels) for installing PyCrypto from a precompiled wheel, and then run `pip install agutil` again.

## Features in development

### agutil.FileType (new class)
* Added `agutil.FileType`, an `argparse` type checker useful for providing as a _type_ argument
to `argparse.ArgumentParser.add_argument`. `FileType` checks that the user's provided
filepath is a valid file with one of the allowed extensions, then returns either
the absolute filepath or a file handle

##### API

* FileType(\*_extensions_, _compression_=`False`, _output_=`None`, \*\*_kwargs_) _(Constructor)_

  Initializes a new `FileType` object. When called on a string, the `FileType` instance
  will check that the string is a valid filepath ending in one of the provided _extensions_.
  If _extensions_ is empty, any valid filepath will be accepted regardless of extension.
  If _compression_ is `True`,
  it will also accept filepaths which end in one of the provided _extensions_ followed
  by ".gz", ".bgz", or ".bz2". If _compression_ is a list, it is taken to be the
  set of allowed compression extensions. _output_ and arbitrary keyword arguments
  control the type of output from calling the `FileType` instance. For descriptions
  of those arguments, see `FileType.__call__`

* FileType.\_\_call\_\_(_arg_) _(Call operator)_

  Checks that the provided _arg_ is a valid filepath and ends in one of the allowed
  _extensions_ (as specified in the constructor). If both of those are true, return
  the absolute filepath for _arg_. Otherwise raise an `argparse.ArgumentTypeError`.
  If _output_ was set to a _String_ in the constructor, this method will return
  a _File-Like object_ instead of an absolute filepath. The value of _output_ is
  used as the _mode_ argument to `open`. Additionally, the value of _kwargs_ in
  the constructor will be unpacked as keyword arguments to `open`.
  If _output_ was a _String_, _arg_ ends in ".gz", ".bgz", or ".bz2", and that
  compression extension existed in the _compression_ argument to the constructor,
  the appropriate compression library will be used to open the file, so that the
  returned _File-Like object_ reads decompressed data. The constructor's _output_
  and _kwargs_ arguments will also be used when opening a compressed file.

### agutil.DirType (new class)
* Added `agutil.DirType`, an `argparse` type checker useful for providing as a _type_ argument
to `argparse.ArgumentParser.add_argument`. `DirType` checks that the user's provided
filepath is a valid directory, then returns the absolute filepath


##### API

* DirType() _(Constructor)_

  Initializes a new `DirType` object. The constructor takes no arguments

* DirType.\_\_call\_\_(_arg_) _(Call operator)_

  Checks that the provided _arg_ is a valid path to a directory and returns the
  absolute filepath. Otherwise it raises an `argparse.ArgumentTypeError`.

### agutil.FOFNType (new class)
* Added `agutil.DirType`, an `argparse` type checker useful for providing as a _type_ argument
to `argparse.ArgumentParser.add_argument`. `FOFNType` checks that the provided argument
is a valid filepath which contains a list of files. Arguments to the constructor
of `FOFNType` configure what is acceptable as a member of the FOFN and how to return
the files

##### API

* FOFNType(\*_extensions_, _min\_paths_=`1`, _as\_list_=`False`, _as\_handle_=`False`, _allow\_direct_=`False`, \*\*_kwargs_) _(Constructor)_

  Initializes a new `FOFNType` instance. _extensions_ should be a list of `str`,
  `FileType`, `DirType`, or `FOFNType` instances, together representing the set
  of acceptable files in the FOFN. Remaining arguments are stored and affect the
  behavior of `FOFNTYPE.__call__`.

* FOFNType.\_\_call\_\_(_arg_) _(Call operator)_

  Checks that the provided _arg_ is a valid filepath. Returns the absolute filepath
  of _arg_.
  If _min\_paths\_ was greater than `0` in the constructor, the file will be opened
  and the first _min\_paths_ lines will be checked against the _extensions_ provided
  in the constructor. If there are less than _min\_paths_ lines or any of the checked
  lines is rejected by all _extensions_, raise an `argparse.ArgumentTypeError`.
  If _as\_list_ is `True`, all lines will be checked and this method will return
  a list of the absolute filepaths contained in the FOFN instead of the absolute
  filepath of _arg_. If _as\_handle_ is `True`, this method will return an open
  _File-Like object_ to _arg_ instead of the absolute filepath. The value of _kwargs_
  in the constructor is unpacked when calling `open`. If both _as\_list_ and _as\_handle_
  were true, this method will return a list of _File-Like objects_ each open to
  one of the files listed in the FOFN. When checking the lines of the FOFN, if
  any of the checks fail (raising an `argparse.ArgumentTypeError`) and _allow\_direct_
  was `True` in the constructor, attempt to check _arg_ directly against the set
  of _extensions_ (instead of treating it like a file containing files to check).
  If _arg_ matches one of the _extensions_, this method continues as if it was parsing
  a FOFN containing _arg_ on one line. In other words, it returns the same result
  that it would return if this method had been called on a filepath to a file
  containing _arg_ and nothing else. Depending on the return type, a temporary
  file may be created, in which case, it will automatically be deleted when the
  interpreter exits
