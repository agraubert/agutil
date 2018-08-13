# agutil
* Master build status: [![Master Build Status](https://travis-ci.org/agraubert/agutil.svg?branch=master)](https://travis-ci.org/agraubert/agutil) [![Live Package Version](https://img.shields.io/pypi/v/agutil.svg)](https://pypi.python.org/pypi/agutil)
* Development build status: [![Dev Build Status](https://travis-ci.org/agraubert/agutil.svg?branch=dev)](https://travis-ci.org/agraubert/agutil) [![Dev Coverage Status](https://coveralls.io/repos/github/agraubert/agutil/badge.svg?branch=dev)](https://coveralls.io/github/agraubert/agutil?branch=dev)

A collection of python utilities

__Version:__ 3.1.2

###### Tools:
* search_range (A utility for manipulating numerical ranges)
* status_bar (A simple progress bar indicator)
* Logger (A class for fast, simple, logging)
* Several standalone utility methods (See the [agutil module page](https://github.com/agraubert/agutil/wiki/agutil-%28main-module%29) on the wiki)

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
* agutil-secure (A command line utility for encrypting and decrypting files)
* Several utility methods for encrypting and decrypting files or file objects

## Documentation:
Detailed documentation of these packages can be found on the [agutil Github wiki page](https://github.com/agraubert/agutil/wiki)

## Feature Removal:

* The `maf2bed` utility and its associated code has been removed

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
* `agutil.byteSize` now supports yottabytes

##### API
* agutil.clump(_seq_, _length_):
* agutil.split_iterable(_seq_, _length_):

  Yields iterables which take from _seq_ in chunks up to _length_.  Each iterable returned will yield up to _length_ items.  If chained together, the iterables returned would iterate the same sequence as _seq_. **Note:** You
  should not use the returned iterables out of order. Each iterable will always
  yield the correct number of elements, but elements will be out of order if you
  do not completely exhaust one iterable before moving to the next

* agutil.splice(_seq_):

  Takes an iterable, _seq_, which yields **N** items, each of length **M** and returns
  a list of **M** generators which each yield **N** items. This is essentially the
  opposite of the builtin `zip`. The width of _seq_ is determined by its first element,
  and `splice` will provide a number of iterators equal to that width.

### agutil.status_bar
The following changes have been made to `agutil.status_bar`:
* Added a `passthrough()` method which takes one argument and returns it unchanged
while incrementing the bar by 1.
* Added a _file_ argument to the `status_bar()` constructor

##### API
* agutil.status_bar.passthrough(_value_):

  Returns _value_ unchaged, but increments the `status_bar` by 1. Useful for updating
  a bar in list certain comprehensions where `status_bar.iter` is infeasible.

* status_bar(_maximum_, _show\_percent_=True, _init_=True, _prepend_="", _append_="", _cols_=int(get\_terminal\_size()[0]/2), _update\_threshold_=.00005, _debugging_=False, _file_=sys.stdout) _(constructor)_

  Creates a new status_bar instance ranging from 0 to _maximum_.
  _show\_percent_ toggles whether or not a percentage meter should be displayed to the right of the bar.
  _init_ sets whether or not the status_bar should immediately display.  If set to false, the bar is displayed at the first update.
  _prepend_ is text to be prepended to the left of the bar.  It will always remain to the left of the bar as the display updates.  **WARNING** Prepended text offsets the bar.  If any part of the bar (including prepended or appended text) extends beyond a single line on the console, the status bar will not display properly.  Prepended text should be kept short.
  _append_ is text to be appended to the right of the bar.  It will always remain to the right of the bar as the display updates.  **WARNING** Appended text extends the display.  If any part of the bar (including prepended or appended text) extends beyond a single line of the console, the status bar will not display properly.  Appended text should be kept short.
  _cols_ sets how long the bar should be.  It defaults to half the terminal size.
  _update\_threshold_ sets the minimum change in percentage to trigger an update to the percentage meter.
  _debugging_ triggers the status_bar to never print to stdout.  If set true, no output will be produced, but exact string of what *would* be displayed is maintained at all times in the _display_ attribute.
  _file_ sets the file object where the status bar will be displayed. Defaults to
  stdout.

### agutil.parallel (module)
The following change has been made to the `agutil.parallel` module:
* The WORKERTYPE constants, `WORKERTYPE_THREAD` and `WORKERTYPE_PROCESS`, have been
updated to reference the actual worker classes, `ThreadWorker` and `ProcessWorker`,
instead of being enumerations for the types. The consequence is that the parallelization
decorators and dispatchers can now be given any class which follows the worker interface
(see changes to dispatchers below for details)

##### Worker Interface
The following is a generic specification for any class which aims to provide a worker
backend for the parallelization system

* Worker(_maximum_) _(constructor)_

  The constructor should take a _maximum_ argument which sets the maximum number
  of jobs which may be run at a time. The Worker is expected to enforce this policy
  and not to actively execute more jobs than the _maximum_

* Worker.work(_func_, _\*args_, _\*\*kwargs_)

  Queues a call to `func(*args, **kwargs)`. The worker is expected to handle jobs
  on its own in such a way that there are never more than the set _maximum_ number
  of active jobs. This method should return a callable which, when called, returns
  the value of `func(*args, **kwargs)` or raises the exception encountered during
  the execution of that call.

* Worker.close()

  It is expected that after calling this function, the worker should no longer accept
  new jobs via `work()`. It is up to the implementation on how this is accomplished
  and whether or not subsequent calls to `work()` raise an exception or return some
  other value. The worker _may_, but is not required to, call this function in `__del__()`

* Worker.is_alive()

  This function should return `True` before `close()` has been called, and `False`
  after.

### agutil.parallel.IterDispatcher
The following changes have been made to the `agutil.parallel.IterDispatcher` class:
* The _workertype_ argument to the constructor may now be any object which follows the
worker interface above. It still defaults to a `ThreadWorker`
* Added `Iterdispatcher.dispatch` as the preferred method for operating the dispatcher,
but operates identically to `IterDispatcher.run`

##### API
* IterDispatcher(_func_, \*_args_, _maximum_=15, _workertype_=WORKERTYPE_THREAD, \*\*_kwargs_): _(constructor)_

  Constructs a new `IterDispatcher` (similar to the old `Dispatcher` object).
  _func_ is the function to be run in the background. _maximum_ is the maximum
  number of background workers that will be allowed to run at once. _workertype_
  sets the type of workers that will be used (threads or processes) and can be any
  class which follows the Worker interface, but it is recommended that you use
  `ThreadWorker` or `ProcessWorker` (provide the class name as the parameter, do not
  provide a class instance).
  The remaining _args_ and _kwargs_ should match the call signature of _func_,
  except that instead of providing single arguments, you should provide **iterables**
  of arguments (and keyword arguments). The iterables will be used to dispatch workers
  in the background, in the order that arguments appear in the iterables

* IterDispatcher.run()
* IterDispatcher.dispatch()

  Begins the execution of the function and returns a **generator**. Once this method
  is called, the `IterDispatcher` will begin pulling arguments out of the argument
  iterables provided in the constructor and start dispatching workers up to the
  maximum allowed number. The generator will yield results from the background
  workers **in the order calls were dispatched**, not in the order that workers
  finish. If an exception is raised during one of the background calls to the function,
  the `IterDispatcher` will raise that exception when it is time to yield the result
  from that particular execution. If an exception is raised (either by a background
  worker, or by the `IterDispatcher` itself) the `IterDispatcher` will halt, and
  no more work will be completed.

### agutil.parallel.DemandDispatcher
The following change has been made to the `agutil.parallel.DemandDispatcher` class:
* The _workertype_ argument to the constructor may now be any object which follows the
worker interface above. It still defaults to a `ThreadWorker`

##### API
* DemandDispatcher(_func_, _maximum_=15, _workertype_=WORKERTYPE_THREAD): _(constructor)_

  Constructs a new `DemandDispatcher`. _func_ is the function to be executed and
  _maximum_ is the maximum number of background workers which can be executed at
  one time. _workertype_ sets the type of workers that will be used (threads or
  processes) and can be any class which follows the Worker interface, but it is
  recommended that you use `ThreadWorker` or `ProcessWorker` (provide the class
  name as the parameter, do not provide a class instance).

### agutil.security (module)
The following change has been made to the `agutil.security` module:
* Added `agutil.security.encryptFileObj` and `agutil.security.decryptFileObj`
methods. These methods take the same arguments as `agutil.security.encryptFile`
and `agutil.security.decryptFile` methods except that they take _file-like_ objects
instead of filenames

##### API
* encryptFileObj(_reader_, _writer_, _cipher_, _validate_=False):

  Encrypts the data read from _reader_ using _cipher_ and writes it to _writer_.
  The cipher is not required to be any class, but it must support an `encrypt()`
  method, which takes a chunk of text, and returns a ciphered chunk.  Padding is
  handled internally (chunks are padded to 16-byte intervals).
  If _validate_ is `True`, encrypt and prepend 16 known bytes to the beginning of the output file.
  This enables file decryption to check the key immediately without decrypting the entire file

* decryptFileObj(_reader_, _writer_, _cipher_, _validate_=False):

  Decrypts the data read from _reader_ using _cipher_ and writes it to _writer_.
  The cipher is not required to be any class, but it must support an `decrypt()`
  method, which takes a chunk of ciphertext, and returns a deciphered chunk.
  Unpadding is handled internally (chunks are padded to 16-byte intervals).
  If _validate_ is `True`, decrypt the first 16 bytes of the file and check against the expected value.
  If the bytes match the expectation, discard them and continue decryption as normal.
  If the bytes do not match, raise a `KeyError`

### agutil.security.SecureConnection
The following change has been made to `agutil.security.SecureConnection`:
* The _retries_ argument of the `send()` function now refers to the number of additional
attempts to send **after** the first fails. Essentially, the maximum number of
attempts to send a message is now _retries_+1 instead of simply _retries_
