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

## Features in Development:

#### agutil.status_bar

The following changes have been made to `agutil.status_bar`:
* The _value_ argument to `status_bar.update()` is now optional. If omitted, the
status bar will be incremented by one
* Added a `status_bar.iter()` class method. The goal of this function is to serve
as a wrapper for iterables to add a status bar to any loop

##### API

* status_bar.iter(cls, iterable, maximum=None, iter_debug=False,\*\*kwargs) _(class method, generator)_

  Takes an _iterable_ and yields elements from it while updating a status bar automatically.
  The _maximum_ argument is used to set the maximum of the created status bar.
  If _maximum_ is omitted or None, `len()` will be called on the iterable to determine
  its size. If _iter\_debug_ is True, this method will first yield the status bar
  before iterating over elements of the provided iterable (for debugging purposes).
  _kwargs_ are passed to the `status_bar` constructor.

* status_bar.update(value=None)

  updates the display iff _value_ would require a change in the length of the progress
  bar, or if it changes the percentage readout by at least _update\_threshold_.
  If _value_ is None, the bar's current value will be incremented by one.
