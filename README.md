# agutil
* Master build status: [![Master Build Status](https://travis-ci.org/agraubert/agutil.svg?branch=master)](https://travis-ci.org/agraubert/agutil) [![Live Package Version](https://img.shields.io/pypi/v/agutil.svg)](https://pypi.python.org/pypi/agutil)
* Development build status: [![Dev Build Status](https://travis-ci.org/agraubert/agutil.svg?branch=dev)](https://travis-ci.org/agraubert/agutil) [![Dev Coverage Status](https://coveralls.io/repos/github/agraubert/agutil/badge.svg?branch=dev)](https://coveralls.io/github/agraubert/agutil?branch=dev)

A collection of python utilities

__Version:__ 2.0.0

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

## Features in development:

## agutil (main module)
The following changes have been made to the `agutil` module:
* Added a `agutil.byteSize()` method to convert a number of bytes to a human-readable string
* Added a new convenience method, `agutil.hashfile()`, to simplify hashing files
* Added two classes for simple shell interaction: `agutil.ShellReturnObject` and `agutil.StdOutAdapter`, which hold shell command output and capture live output, respectively.
* Added a new convenience method, `agutil.cmd`, to simplify executing shell commands programatically.

##### API
* agutil.hashfile(_filepath_, _algorithm_='sha1', _length_=None):

  Opens the file at the requested _filepath_ and generates a hash using the specified
  _algorithm_.  If _filepath_ cannot be found, it raises a `FileNotFoundError`.
  If _algorithm_ is not available on the current platform, it raises a `ValueError`.
  If _length_ is provided and is not None, it is passed to `algorithm.digest()`
  for variable length digest algorithms (**shake_128** and **shake_256**)

* agutil.byteSize(_n_):

  Returns a string with _n_ converted to the highest unit of Bytes where _n_ would
  be at least 1 (caps at ZiB), rounded to 1 decimal place.  Examples:

  * byteSize(1) = `1B`
  * byteSize(1023) = `1023B`
  * byteSize(1024) = `1KiB`
  * byteSize(856633344) = `816.9MiB`
  * byteSize(12379856472314232739172) = `10.5ZiB`


* agutil.cmd(_expr_, _display_=True):

  Executes _expr_ in a background shell and returns a `agutil.ShellReturnObject` afterwards.
  _expr_ can either be a single command string, or a list/tuple of command arguments
  (which will be quoted and escaped if necessary).
  If _display_ is True, the stdout and stderr from the background shell will be
  displayed live in the interpreter in addition to being captured in the
  returned `agutil.ShellReturnObject`

## agutil.STDOUTADAPTER
This class acts to record any data written to its file descriptor.
After constructing a new `StdOutAdapter` instance, other programs may write to `StdOutAdapter.writeFD`.

##### API
* StdOutAdapter(_display_) _(constructor)_

  Constructs a new `StdOutAdapter` instance.  Write data to the instance's
  `writeFD` attribute to have the instance record it.  If _display_ is True,
  any data written to `writeFD` will be copied to StdOut in addition to being recorded.

* StdOutAdapter.kill()

  Closes the internal duplexed file descriptors. No further data can be
  written to `writeFD` and the adapter will no longer read any data.
  This must be called before calling `StdOutAdapter.readBuffer()`

* StdOutAdapter.readBuffer()

  Returns a Bytes object representing the exact sequence of Bytes written
  to `writeFD` before the descriptor was closed. You must call `kill()` before calling this method.
  If the `StdOutAdapter` is still alive, this method returns an empty string.

## agutil.SHELLRETURNOBJECT
This class represents the results of executing a command from the shell using `agutil.cmd()`.

##### API

* agutil.ShellReturnObject(_command_, _stdoutAdapter_, _returncode_) _(constructor)_

  **Calling this method directly is not recommended**.
  The prefered method of creating a `ShellReturnObject` is to call `agutil.cmd()` with a shell command.

  Returns a new `ShellReturnObject` instance.  _command_ and _returncode_ simply set the `command` and `returncode` attributes of the `ShellReturnObject`.
  The `rawbuffer` attribute will contain the exact byte buffer of the provided _stdoutAdapter_, and the `buffer` attribute will contain the same, but with backspace characters parsed out (and the associated prior characters removed)

## agutil.status_bar
The following change has been made to the `agutil.status_bar` class:
* The _show_percent_ parameter to the constructor now defaults to `True`

##### API

* status_bar(maximum, show_percent = True, init=True, prepend="", append="", cols=int(get_terminal_size()[0]/2), update_threshold=.00005, debugging=False) _(constructor)_
  Creates a new status_bar instance ranging from 0 to _maximum_

  _show\_percent_ toggles whether or not a percentage meter should be displayed to the right of the bar

  _init_ sets whether or not the status_bar should immediately display.  If set to false, the bar is displayed at the first update

  _prepend_ is text to be prepended to the left of the bar.  It will always remain to the left of the bar as the display updates.  **WARNING** Prepended text offsets the bar.  If any part of the bar (including prepended or appended text) extends beyond a single line on the console, the status bar will not display properly.  Prepended text should be kept short

  _append_ is text to be appended to the right of the bar.  It will always remain to the right of the bar as the display updates.  **WARNING** Appended text extends the display.  If any part of the bar (including prepended or appended text) extends beyond a single line of the console, the status bar will not display properly.  Appended text should be kept short

  _cols_ sets how long the bar should be.  It defaults to half the terminal size

  _update\_threshold_ sets the minimum change in percentage to trigger an update to the percentage meter

  _debugging_ triggers the status_bar to never print to stdout.  If set true, no output will be produced, but exact string of what *would* be displayed is maintained at all times in the _display_ attribute

## agutil.security.SECURECONNECTION
The following change has been made to the `agutil.security.SecureConnection` class:
* `savefile()` timeout now applies to each chunk of the file.  The operation will
block so long as the remote socket sends at least one chunk per timeout period.
(API unchanged)

## agutil-secure
The following change has been made to the `agutil-secure` console script:
* The multiple _input_ files can now be provided.  This allows `agutil-secure` to
handle globs

##### COMMAND USAGE
* `agutil-secure [-h] [-p PASSWORD] [-o OUTPUT] [--py33] [-f] [-v] {encrypt,decrypt}
input [input...]`

  positional arguments:
    * _{encrypt,decrypt}_:     Sets the mode to either encryption or decryption
    * _input_:                 Input file(s) to encrypt or decrypt

  optional arguments:
    * _-h, --help_:            show this help message and exit
    * _-p PASSWORD, --password PASSWORD_:
                          The password to encrypt or decrypt with. Note:
                          passwords containing (spaces) must be encapsulated
                          with quotations ("")
    * _-o OUTPUT, --output OUTPUT_:
                          Where to save the encrypted or decrypted file(s). If
                          omitted, agutil-secure will replace the input file(s).
                          If any output files are provided, you must provide the
                          same number of outputs as inputs, by providing the -o
                          argument multiple times
    * _--py33_:                Forces encryption or decryption to use the simplified,
                          3.3 compatable pbkdf2_hmac
    * _-f, --force_:           Attempts to decrypt the file without verifying the
                          password. Files encrypted with agutil version 1.1.3
                          and earlier MUST be decrypted with this option
    * _-v, --verbose_:         Display the progress of the operation
