# agutil
* Master build status: [![Master Build Status](https://travis-ci.org/agraubert/agutil.svg?branch=master)](https://travis-ci.org/agraubert/agutil) [![Live Package Version](https://img.shields.io/pypi/v/agutil.svg)](https://pypi.python.org/pypi/agutil)
* Development build status: [![Dev Build Status](https://travis-ci.org/agraubert/agutil.svg?branch=dev)](https://travis-ci.org/agraubert/agutil) [![Dev Coverage Status](https://coveralls.io/repos/github/agraubert/agutil/badge.svg?branch=dev)](https://coveralls.io/github/agraubert/agutil?branch=dev)

A collection of python utilities

__Version:__ 1.1.3

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

## Features in Development:

## agutil-secure
The following changes have been made to the `agutil-secure` console script:
* The _password_ parameter is now optional.  By default, `agutil-secure` will now prompt
the user for a password (in a secure manner) if it is not provided. When prompting for a password,
the characters typed will not display on screen (unless the secure method of password input
is not available on your platform, in which case a warning will be displayed that passwords
will be visible).  Passwords can still be provided on the command line with _-p \<password\>_ or _--password \<password\>_.
Passwords provided as command line arguments will still be visible.
* The _output_ parameter is now optional.  By default, `agutil-secure` will now perform operations
in-place, overwriting the input file with the new data.  Use _-o \<filename\>_ or _--output \<filename\>_ to
save the output to `filename`
* `agutil-secure` now validates files before decrypting.  If the password is incorrect,
decryption halts and returns a status code of `1`.  Must use _-f_ parameter to decrypt
files encrypted with previous versions of `agutil-secure`
* Added _-f_/_--force_ option to maintain compatibility with previous versions.
Use _-f_ if decryption fails when decrypting files encrypted with old versions of `agutil-secure`
* Added _-v_/_--verbose_ option to display the progress of the current operation

## security.ENCRYPTFILE and security.DECRYPTFILE
The following change has been made to both `agutil.security.encryptFile` and `agutil.security.decryptFile`:
* Added a _validate_ argument (defaults to `False`):
  * For `encryptFile`, if _validate_ is `True`, encrypt and prepend 16 known bytes to the beginning of the output file.
  * For `decryptFile`, if _validate_ is `True`, decrypt the first 16 bytes of the file and check against the expected value.  If the bytes match the expectation, discard them and continue decryption as normal.  If the bytes do not match, raise a `KeyError`

##### API
* encryptFile(input\_filename, output\_filename, cipher, validate=False)
  Encrypts the file specified by _input\_filename_ and saves it to _output\_filename_ using _cipher_.
  The cipher is not required to be any class, but it must support an `encrypt()` method, which takes a chunk of text, and returns a ciphered chunk.  Padding is handled internally (chunks are padded to 16-byte intervals).
  If _validate_ is `True`, encrypt and prepend 16 known bytes to the beginning of the output file.

* decryptFile(input_filename, output\_filename, cipher, validate=False)
  Decrypts the file specified by _input\_filename_ and saves it to _output\_filename_ using _cipher_.
  The cipher is not required to be any class, but it must support an `decrypt()` method, which takes a chunk of ciphertext, and returns a deciphered chunk.  Unpadding is handled internally (chunks are padded to 16-byte intervals).
  If _validate_ is `True`, decrypt the first 16 bytes of the file and check against the expected value.
  If the bytes match the expectation, discard them and continue decryption as normal.  If the bytes do not match, raise a `KeyError`
