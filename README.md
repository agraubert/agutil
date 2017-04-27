# agutil
* Master build status: [![Master Build Status](https://travis-ci.org/agraubert/agutil.svg?branch=master)](https://travis-ci.org/agraubert/agutil) [![Live Package Version](https://img.shields.io/pypi/v/agutil.svg)](https://pypi.python.org/pypi/agutil)
* Development build status: [![Dev Build Status](https://travis-ci.org/agraubert/agutil.svg?branch=dev)](https://travis-ci.org/agraubert/agutil) [![Dev Coverage Status](https://coveralls.io/repos/github/agraubert/agutil/badge.svg?branch=dev)](https://coveralls.io/github/agraubert/agutil?branch=dev)

A collection of python utilities

__Version:__ 1.2.0

###### Tools:
* search_range (A utility for manipulating numerical ranges)
* status_bar (A simple progress bar indicator)
* Logger (A class for fast, simple, logging)
* Several standalone utility methods (See the [agutil module page](https://github.com/agraubert/agutil/wiki/agutil-%28main-module%29) on the wiki)

The __bio__ package:

* maf2bed (A command line utility for parsing a .maf file and converting coordinates from 1-based (maf standard) to 0-based (bed standard))
* tsvmanip (A command line utility for filtering, rearranging, and modifying tsv files)

The __io__ package:

* Socket (A low-level network IO class built on top of the standard socket class)
* SocketServer (A low-level listen server to accept connections and return Socket classes)
* QueuedSocket (A low-level network IO class built to manage input across multiple channels)

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

## agutil (main module)
The following changes have been made to the `agutil` module:
* Added a `agutil.byteSize()` method to convert a number of bytes to a human-readable string
* Added a new convenience method, `agutil.hashfile()`, to simplify hashing files

##### API
* agutil.hashfile(_filepath_, _algorithm_='sha1', _length_=None):

  Opens the file at the requested _filepath_ and generates a hash using the specified
  _algorithm_.  If _filepath_ cannot be found, it raises a `FileNotFoundError`.
  If _algorithm_ is not available on the current platform, it raises a `ValueError`.
  If _length_ is provided and is not None, it is passed to `algorithm.digest()`
  for variable length digest algorithms (**shake_128** and **shake_256**)

* byteSize(_n_):

  Returns a string with _n_ converted to the highest unit of Bytes where _n_ would
  be at least 1 (caps at ZiB), rounded to 1 decimal place.  Examples:

  * byteSize(1) = `1B`
  * byteSize(1023) = `1023B`
  * byteSize(1024) = `1KiB`
  * byteSize(856633344) = `816.9MiB`
  * byteSize(12379856472314232739172) = `10.5ZiB`

## agutil.security.SECURECONNECTION
The following change has been made to the `agutil.security.SecureConnection` class:
* `savefile()` timeout now applies to each chunk of the file.  The operation will
block so long as the remote socket sends at least one chunk per timeout period.
(API unchanged)
