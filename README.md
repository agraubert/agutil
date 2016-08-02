# agutil
* Master build status: [![Master Build Status](https://travis-ci.org/agraubert/agutil.svg?branch=master)](https://travis-ci.org/agraubert/agutil) [![Live Package Version](https://img.shields.io/pypi/v/agutil.svg)](https://pypi.python.org/pypi/agutil)
* Development build status: [![Dev Build Status](https://travis-ci.org/agraubert/agutil.svg?branch=dev)](https://travis-ci.org/agraubert/agutil) [![Dev Coverage Status](https://coveralls.io/repos/github/agraubert/agutil/badge.svg?branch=dev)](https://coveralls.io/github/agraubert/agutil?branch=dev)

A collection of python utilities

__Version:__ 0.6.1b

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

##Documentation:
Detailed documentation of these packages can be found on the [agutil Github wiki page](https://github.com/agraubert/agutil/wiki)

##Installation note:
This package requires PyCrypto, which typically has issues compiling on windows.  If you are on windows and `pip install agutil` fails during the installation of PyCrypto, then follow the instructions [here](https://github.com/sfbahr/PyCrypto-Wheels) for installing PyCrypto from a precompiled wheel, and then run `pip install agutil` again.

##Features in development:

##security.SECURECONNECTION
The following changes have been made to the `SecureConnection` API:
The _timeout_ parameter for the `read()`, `savefile()`, `shutdown()`, and `close()` methods now default to -1.  A value of -1 for the timeout uses the default timeout provided in the constructor.

#####API
* SecureConnection.read(decode=True, timeout=-1)
  Returns the oldest unread message received, or waits until a message is received.  If _decode_ is True, the received bytes object is decoded into a str object before returning.  If _timeout_ is not None, this is the maximum amount of time, in seconds, to wait for an incoming message (raises a socket.timeout exception if no message is received in time).  If _timeout_ is None, `read()` will block indefinitely until a message is received

* SecureConnection.savefile(destination, timeout=-1, force=False)
  Processes the oldest pending file transfer request or waits up to _timeout_ seconds to receive a request.  If _force_ is True, the request is automatically accepted, otherwise the user is prompted to accept or deny the request.  If the request is accepted (either by _force_ or manual acceptance) it is decrypted and saved to _destination_

* SecureConnection.shutdown(timeout=-1)
* SecureConnection.close(timeout=-1)
  Closes the connection.  The `SecureConnection` immediately stops accepting new commands from both the user and the remote socket (but currently queued or running tasks are allowed to queue new tasks).  Waits up to _timeout_ seconds for all currently runnning tasks to complete.  Then (regardless of if all tasks completed or not) it prevents any new tasks from being queued.  Lastly, the internal `SecureSocket` connection is closed.

##security.SECURESOCKET
The following change has been made to the `SecureSocket` API:
The constructor _timeout_ parameter is now required to be None or a non-negative integer.  A TypeError is raised otherwise.

#####API
* SecureSocket(socket, password=None, rsabits=4096, timeout=3, logmethod=DummyLog) _(constructor)_
  Initializes an `agutil.security.SecureSocket` object around an `agutil.io.Socket` instance.
  Generates a new RSA keypair of _rsabits_ size, and exchanges public keys with the remote socket (which must also be a `SecureSocket`).
  If _password_ is set, and not None, it is used to generate an AES ECB cipher which is used to encrypt all basic communications between the sockets (the remote socket must use the same password).
  _timeout_ sets the default timeout for receiving incoming messages (must be None or a non-negative integer).
  _logmethod_ specifies a logging object to use.  It defaults to `agutil.DummyLog` (which does not log anything).  _logmethod_ may either be an `agutil.Logger` class, or a bound method returned by `agutil.Logger.bindToSender()`.

* SecureSocket.send(msg, channel='__rsa__')
* SecureScoket.sendRSA(msg, channel='__rsa__')
  Encrypts _msg_ using the remote socket's public key and sends over the channel _channel_.  If _msg_ is longer than the remote public key can encrypt, it is broken into chunks and each chunk is encrypted before transmission.

* SecureSocket.recv(channel='__rsa__', decode=False, timeout=-1)
* SecureSocket.recvRSA(channel='__rsa__', decode=False, timeout=-1)
  Waits to receive a message on the _channel_ channel, then decrypts using this socket's private key.  If _decode_ is true, the decrypted bytes object is decoded into a str object.  _timeout_ sets the maximum time allowed for any single operation with the remote socket (thus the `.recvRSA` method may take longer to complete as a whole).  If _timeout_ is -1, it defaults to the `SecureSocket`'s default timeout parameter

* SecureSocket.sendAES(msg, channel='__aes__', key=False, iv=False)
  Encrypts _msg_ using an AES cipher and sends to the remote socket over the channel _channel_.  If _msg_ is a `BytesIO` object, bytes will be read from the file and transmitted, instead of transmitting _msg_ itself.  If both _key_ and _iv_ are False, the cipher used for encryption is the same as the `SecureSocket`'s base cipher (an ECB cipher if _password_ was set in the constructor, or no cipher at all otherwise).  If _key_ is True or a bytes object, the cipher used for encryption is an AES ECB cipher using _key_ as the key (if _key_ is true, a random 32-byte key is generated).  If both _key_ and _iv_ are True or bytes objects, the cipher used for encryption is an AES CBC cipher using _key_ as the key and _iv_ as the initialization vector (if _key_ is true, a random 32-byte key is generated; if _iv_ is true, a random 16-byte vector is generated).  If an AES cipher is used that isn't the socket's base cipher, the _key_ is transmitted using the `.sendRSA` method

* SecureScoket.recvAES(channel='__aes__', decode=False, timeout=-1, output_file=None)
  Waits to receive a message on _channel_ then decrypts using an AES cipher.  The type of cipher used is determined by the sending socket.  _timeout_ behaves identical to how it does in `.recvRSA`.  If output_file is a BytesIO object, the decrypted data is written to that file.  If it is a str object, that is used as a filename to output the decrypted data.  Otherwise, the decrypted data is returned.  If _decode_ is True and _output\_file_ is None, then the decrypted bytes object is encoded to a str object before returning

* SecureSocket.sendRAW msg, channel='__raw__')
  Sends _msg_ over the channel _channel_ with no encryption

* SecureSocket.recvRAW(channel='__raw__', decode=False, timeout=-1)
  Waits to receive a message on _channel_ then returns.  Waits at most _timeout_ seconds (or the default timeout of the `SecureSocket` if timeout is -1).  If _decode_ is True, then the received bytes object is decoded into a str object before returning

* SecureSocket.settimeout(timeout)
  Sets the default timeout to _timeout_

* SecureSocket.gettimeout()
  Returns the current default timeout

* SecureSocket.close()
  Closes the underlying `Socket` and terminates the connection
