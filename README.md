# agutil
* Master build status: [![Master Build Status](https://travis-ci.org/agraubert/agutil.svg?branch=master)](https://travis-ci.org/agraubert/agutil) [![Live Package Version](https://img.shields.io/pypi/v/agutil.svg)](https://pypi.python.org/pypi/agutil)
* Development build status: [![Dev Build Status](https://travis-ci.org/agraubert/agutil.svg?branch=dev)](https://travis-ci.org/agraubert/agutil) [![Dev Coverage Status](https://coveralls.io/repos/github/agraubert/agutil/badge.svg?branch=dev)](https://coveralls.io/github/agraubert/agutil?branch=dev)

A collection of python utilities

__Version:__ 3.0.0

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

* parallelize (A decorator to easily convert a regular function into a parallelized version)
* parallelize2 (A similar parallelization decorator with a slightly different flavor)
* IterDispatcher (Logical backend for dispatching calls with parallelize)
* DemandDispatcher (Logical backend for dispatching calls with parallelize2)
* ThreadWorker (Task management backend for dispatching parallel calls to threads)
* ProcessWorker (Task management backend for dispatching parallel calls to processes)

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

### agutil.io.SocketServer
The following change has been made to `agutil.io.SocketServer`:
* The `accept()` method now takes a `socket_type` argument to determine which type of Socket in the `agutil` socket class tree will be returned.
The method also takes a variable number of keyword arguments which will be passed to the returned socket's constructor. The method defaults
to returning `agutil.io.Socket` instances

##### API
* agutil.io.SocketServer(_socket\_type_=agutil.io.Socket, \*\*_kwargs_):

  Blocks until an incoming connection is established, then returns an object for the incoming connection of type
  _socket\_type_. The type defaults to `agutil.io.Socket`. Any _kwargs_ are sent to the constructor of the
  returned socket.

### agutil.io.QueuedSocket
The following changes have been made to `agutil.io.QueuedSocket`:
* The constructor no longer takes an `agutil.io.Socket` as argument, but instead takes an address and port, like `agutil.io.Socket`
* Outgoing messages are no longer sent in a FIFO order. The socket will continuously rotate
through all channels waiting to send messages, sending one message from each (in FIFO).


##### API
* agutil.io.QueuedSocket(_address_, _port_, _logmethod_=agutil.DummyLog) _(Constructor)_

  _address_ and _port_ are used to establish a connection to a remote socket.
  _logmethod_ specifies a logging object to use (it defaults to `agutil.DummyLog`),
  but may also be an `agutil.Logger` instance or a bound method returned by
  `agutil.Logger.bindToSender()`.

### agutil.security.SecureSocket
The following change has been made to `agutil.security.SecureSocket`:
* The constructor no longer takes an `agutil.io.Socket` as an argument, but instead takes an address and port, like `agutil.io.Socket`

##### API
* agutil.security.SecureSocket(_address_, _port_, _password_=None, _rsabits_=4096, _timeout_=3, _logmethod_=agutil.DummyLog) _(Constructor)_

  _address_ and _port_ are used to establish a connection to a remote socket.
  If _password_ is set and not None, it is used to generate a new AES ECB cipher
  which provides the lowest level of encryption for the socket (used for basic
  communications between the sockets). Both sockets must use the same _password_.
  _rsabits_ sets the size of the RSA keypair used for exchanging RSA messages with
  the remote socket.  _timeout_ sets the default timeout for receiving incoming
  messages (must be None, or a non-negative integer). _logmethod_ specifies a
  logging object to use (it defaults to `agutil.DummyLog`), but may also be an
  `agutil.Logger` instance or a bound method returned by `agutil.Logger.bindToSender()`.

### agutil (Main Module)
The following changes have been made to the main `agutil` module:
* `agutil.split_iterable` is now also available as `agutil.clump` which was chosen
as it more clearly describes the function. `agutil.split_iterable` _may_ be removed
in a future release, but this is not yet planned
* Added a function `agutil.splice` which takes a iterable of at least 2 dimensions (M rows by N columns)
and returns an iterable for each column (N iterables of length M).

##### API
* agutil.clump(_seq_, _length_):
* agutil.split_iterable(_seq_, _length_):

  Yields iterables which take from _seq_ in chunks up to _length_.  Each iterable returned will yield up to _length_ items.  If chained together, the iterables returned would iterate the same sequence as _seq_. **Note:** You
  should not use the returned iterables out of order. Each iterable will always
  yield the correct number of elements, but elements will be out of order if you
  do not completely exhaust one iterable before moving to the next

### agutil.status_bar
The following change has been made to `agutil.status_bar`:
* Added a `passthrough()` method which takes one argument and returns it unchanged
while incrementing the bar by 1.

##### API
* agutil.status_bar.passthrough(_value_):

  Returns _value_ unchaged, but increments the `status_bar` by 1. Useful for updating
  a bar in list certain comprehensions where `status_bar.iter` is infeasible.
