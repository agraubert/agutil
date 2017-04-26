# CHANGELOG

## 1.2.0

#### agutil-secure
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

#### security.ENCRYPTFILE and security.DECRYPTFILE
The following change has been made to both `agutil.security.encryptFile` and `agutil.security.decryptFile`:
* Added a _validate_ argument (defaults to `False`):
  * For `encryptFile`, if _validate_ is `True`, encrypt and prepend 16 known bytes to the beginning of the output file.
  * For `decryptFile`, if _validate_ is `True`, decrypt the first 16 bytes of the file and check against the expected value.  If the bytes match the expectation, discard them and continue decryption as normal.  If the bytes do not match, raise a `KeyError`

## 1.1.2 and 1.1.3

Documentation errors fixed.  Automated release system required new versions bumped to push changes to pypi

## 1.1.1

#### io.QueuedSocket The following change has been made to the agutil.io.queuedsocket api:

* Added a flush() method


#### security.SECURECONNECTION The following change has been made to the agutil.security.secureconnection api:

* Added a flush() method

## 1.1.0

#### STATUS_BAR
The following changes have been made to the `agutil.status_bar` api:
- Status bar now supports the context manager protocol.  The bar is immediately initialized on entry, and automatically cleared on exit
- The `status_bar.clear()` method now defaults to _erase_=True
- Fixed a bug which occurs when running a status bar in reverse, where trailing percent signs would be left as the display shortened

## 1.0.0

#### security.SECURECONNECTION
The following changes have been made to the `SecureConnection` API:
* The _timeout_ parameter for the `read()`, `savefile()`, `shutdown()`, and `close()` methods now default to -1.  A value of -1 for the timeout uses the default timeout provided in the constructor.

#### security.SECURESOCKET
The following change has been made to the `SecureSocket` API:
* The constructor _timeout_ parameter is now required to be None or a non-negative integer.  A TypeError is raised otherwise.

# Pre-Release Versions

## 0.6.0b

#### LOGGER (Added new class)
* The `agutil` module includes the `Logger` class, which provides a simple interface for quick logging.  Messages can be logged over specific channels, and each channel can be set to log to a file, stdout, neither, or both.  The actual `Logger` instance is meant to be the point of control for the log.  All `agutil` classes which support logging will log messages through the lambda returned by `Logger.bindToSender()`.

* Note: `agutil` also includes `DummyLog`, a default log used in other `agutil` classes which does no actual logging or printing

#### STATUS_BAR
The following change has been made to the `agutil.status_bar` api:
* The _transcript_ parameter has been removed from the constructor.  The status_bar no longer supports logging a transcript of activity.

#### io.QUEUEDSOCKET
The following change has been made to the `agutil.io.QueuedSocket` API:
* A _logmethod_ parameter has been added to the constructor

#### security.SECURECONNECTION
The following change has been made to the `agutil.security.SecureConnection` API:
* A _logmethod_ parameter has been added to the constructor, and the _verbose_ parameter has been removed

#### security.SECURESOCKET
The following change has been made to the `agutil.security.SecureSocket` API:
* A _logmethod_ parameter has been added to the constructor, and the _verbose_ parameter has been removed

#### security.SECURESERVER
The following change has been made to the `agutil.security.SecureServer` API:
* A _logmethod_ parameter has been added to the constructor, and the _childverbose_ parameter has been removed

#### security.AGUTIL-SECURE (Added new console entry-point)
* The `agutil.security` module provides a command line interface for encrypting and decrypting files.

#### agutil utility methods (Added new methods in `agutil` module)
* agutil.intToBytes(num, padding\_length=0)

* agutil.bytesToInt(num)

* agutil.byte_xor(b1, b2)

* agutil.split_iterable(seq, length)

## 0.5.0b

#### io.QUEUEDSOCKET (Added new class)
* The `agutil.io` module includes the class `QueuedSocket` which wraps a regular `agutil.io.Socket` class.
* `QueuedSocket` instances are designed to allow multiple threads to utilize the same socket by dividing data across multiple channels.
* The `.send()` and `.recv()` methods now take an (optional) additional _channel_ argument compared to the methods on a regular `agutil.io.Socket` instance (API below).  `.send()` and `.recv()` will send and receive data across the specified channel.

#### io.SOCKET
The following change has been made to the `agutil.io.Socket` API:

* Added a `gettimeout` method to get the timeout of the underlying socket

#### security.SECURESOCKET
The following change has been made to the `agutil.security.SecureSocket` API:

* The previous `agutl.security.SecureSocket` class has been removed and replaced with a completely overhauled class.  For a class similar to the old `SecureSocket` see: `SecureConnection`.

* The `agutil.security` module includes the `SecureSocket` class, which wraps over an `agutil.io.Socket` instance.
A `SecureSocket` class allows for encrypted communications using RSA or AES encryption.

#### security.SECURECONNECTION (Added new class)
* The `agutil.security` module includes the `SecureConnection` class which provides a high-level interface for sending and receiving secure messages and files.  All tasks are run in background threads, each exchanging data over a different channel on the underlying SecureSocket, allowing for many simultaneous tasks to be run.

#### security.SECURESERVER (Added new class)
* The `agutil.security` module includes the `SecureServer` class, which is similar to the `agutil.io.SocketServer` class, but it returns `SecureConnection` instances instead of `Socket` instances.

#### security.ENCRYPTFILE security.DECRYPTFILE (Added new methods to the `agutil.security` module)
* The `agutil.security` module includes two methods for file encryption and decryption: `encryptFile()` and `decryptFile()`.

## 0.4.1b

#### security.SECURESOCKET

The following change has been made to the `agutil.security.SecureSocket` api:

* `agutil.security.new()` can be used as an alias to construct a SecureSocket

## 0.4.0b

#### security.NEW (Added new method to the `agutil.security` module)
* security.NEW (method) The agutil.security module includes the new() method, which is a wrapper for the SecureSocket constructor. new() can be used to construct both ends of a SecureSocket connection, without the need for two methods with different API's. new() is the preferred method for constructing a SecureSocket, and so the actual constructor will not be documented

---

Changes prior to 0.4.0b are not recorded