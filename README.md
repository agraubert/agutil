# agutil
* Master build status: [![Master Build Status](https://travis-ci.org/agraubert/agutil.svg?branch=master)](https://travis-ci.org/agraubert/agutil) [![Live Package Version](https://img.shields.io/pypi/v/agutil.svg)](https://pypi.python.org/pypi/agutil)
* Development build status: [![Dev Build Status](https://travis-ci.org/agraubert/agutil.svg?branch=dev)](https://travis-ci.org/agraubert/agutil) [![Dev Coverage Status](https://coveralls.io/repos/github/agraubert/agutil/badge.svg?branch=dev)](https://coveralls.io/github/agraubert/agutil?branch=dev)

A collection of python utilities

__Version:__ 3.1.2

###### Tools:
* search_range (A utility for manipulating numerical ranges)
* status_bar (A simple progress bar indicator)
* Logger (A class for fast, simple, logging)
* ActiveTimeout (A class for enforcing a timeout for a set of operations)
* Several standalone utility methods (See the [agutil module page](https://github.com/agraubert/agutil/wiki/agutil-%28main-module%29) on the wiki)

The __io__ package:

* Socket (A low-level network IO class built on top of the standard socket class)
* SocketServer (A low-level listen server to accept connections and return Socket classes)
* MPlexSocket (A low-level network IO class which multiplexes I/O through multiple channels. Threadless version of `QueuedSocket`)
* ~~QueuedSocket (A low-level network IO class built to manage input across multiple channels)~~

  **Deprecated: Will be removed in a future release.** Please transition to `agutil.io.MPlexSocket` which is a threadless version of the same interface

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
* EncryptionCipher and DecryptionCipher (Twin classes for agutil's modular encryption format)
* Several other utility functions and classes for encrypting and decrypting data

## Documentation:
Detailed documentation of these packages can be found on the [agutil Github wiki page](https://github.com/agraubert/agutil/wiki)

## Feature Removal:

* The `maf2bed` utility and its associated code has been removed

## Deprecation Notice:

* `agutil.io.QueuedSocket` is now deprecated in favor of `agutil.io.MPlexSocket`

## Features in Development:

### agutil.io.SocketServer
The following change has been made to `agutil.io.SocketServer`:
* The `accept()` method now takes a `socket_type` argument to determine which type of Socket in the `agutil` socket class tree will be returned.
The method also takes a variable number of keyword arguments which will be passed to the returned socket's constructor. The method defaults
to returning `agutil.io.Socket` instances

##### API
* agutil.io.SocketServer(_socket\_type_=`agutil.io.Socket`, \*\*_kwargs_):

  Blocks until an incoming connection is established, then returns an object for the incoming connection of type
  _socket\_type_. The type defaults to `agutil.io.Socket`. Any _kwargs_ are sent to the constructor of the
  returned socket.

### agutil.io.QueuedSocket
The following changes have been made to `agutil.io.QueuedSocket`:
* **Deprecation Notice:** `agutil.io.QueuedSocket` is now deprecated in favor of `agutil.io.MPlexSocket`. The latter provides the same interface but in a lighter-weight and threadless manner.
* The constructor no longer takes an `agutil.io.Socket` as argument, but instead takes an address and port, like `agutil.io.Socket`
* Outgoing messages are no longer sent in a FIFO order. The socket will continuously rotate
through all channels waiting to send messages, sending one message from each (in FIFO).


##### API
* agutil.io.QueuedSocket(_address_, _port_, _logmethod_=`agutil.DummyLog`) _(Constructor)_

  _address_ and _port_ are used to establish a connection to a remote socket.
  _logmethod_ specifies a logging object to use (it defaults to `agutil.DummyLog`),
  but may also be an `agutil.Logger` instance or a bound method returned by
  `agutil.Logger.bindToSender()`.

### agutil.io.MPlexSocket (new class)
This class provides the same interface as `agutil.io.QueuedSocket` but does so without
the use of background threads. It is meant to serve as a drop-in replacement, but
due to the significance of the change, it was written as a new class.
`agutil.security.SecureSocket` now derives from this class

##### API
* MPlexSocket(_address_, _port_, _logmethod_=`agutil.DummyLog`): _(Constructor)_

  Constructs a new `agutil.io.MPlexSocket`. _address_ and _port_ are used to establish a connection to a remote socket.
  _logmethod_ specifies a logging object to use (it defaults to `agutil.DummyLog`), but may also be an `agutil.Logger` instance or a
  bound method returned by `agutil.Logger.bindToSender()`

* MPlexSocket.close():

  Closes the socket

* MPlexSocket.flush():

  This is a no-op added for compatability with the `agutil.io.QueuedSocket` api

* MPlexSocket.use\_timeout(_t_): _(Context Manager)_

  This function returns a context manager which sets the socket timeout to _t_ when entering, and resets it to its previous value when exiting.
  _t_ may be a positive number of seconds or `None`

* MPlexSocket.send(_message_, _channel_=`'__orphan__'`):

  Sends _message_ over the specified _channel_. If the _channel_ argument is omitted, it sends it over a default channel.
  Channel names **cannot** contain the carrot character (`^`, ascii 94), which is used as a delimiter for encoding the channel name.

* MPlexSocket.recv(_channel_=`'__orphan__'`, _decode_=`False`, _timeout_=`None`):

  Attempts to receive a message from the specified _channel_, or blocks until a message is available. If _decode_ is `True`, the byes object will be decodes into a string when returned. If a _timeout_ is specified and not `None`, the method will block for at most approximately _timeout_ seconds, then raise a `socket.Timeout` exception.

### agutil.security.SecureSocket
The following changes have been made to `agutil.security.SecureSocket`:
* The constructor no longer takes an `agutil.io.Socket` as an argument, but instead takes an address and port, like `agutil.io.Socket`
* This class now derives from `agutil.io.MPlexSocket` instead of `agutil.io.QueuedSocket`
* Added _sign_ argument to `sendRSA()`. `sendRSA()` and `recvRSA()` now handle signature
validation internally
* SecureSocket now uses `agutil.security.EncryptionCipher` and `agutil.security.EncryptionCipher`
  as backends for `sendAES()` and `recvAES()`.

##### API
* SecureSocket(_address_, _port_, _password_=`None`, _rsabits_=`4096`, _timeout_=`3`, _logmethod_=`agutil.DummyLog`) _(Constructor)_

  _address_ and _port_ are used to establish a connection to a remote socket.
  If _password_ is set and not None, it is used to generate a new AES ECB cipher
  which provides the lowest level of encryption for the socket (used for basic
  communications between the sockets). Both sockets must use the same _password_.
  _rsabits_ sets the size of the RSA keypair used for exchanging RSA messages with
  the remote socket.  _timeout_ sets the default timeout for receiving incoming
  messages (must be None, or a non-negative integer). _logmethod_ specifies a
  logging object to use (it defaults to `agutil.DummyLog`), but may also be an
  `agutil.Logger` instance or a bound method returned by `agutil.Logger.bindToSender()`.

* SecureSocket.send(_msg_, _channel_=`'\_\_rsa\_\_'`, _sign_=`'SHA-256'`)
* SecureScoket.sendRSA(_msg_, _channel_=`'\_\_rsa\_\_'`, _sign_=`'SHA-256'`)
  Encrypts _msg_ using the remote socket's public key and sends over the channel _channel_.
  If _msg_ is longer than the remote public key can encrypt, it is broken into
  chunks and each chunk is encrypted before transmission. _sign_ can be `False`,
  or one of `'MD5'`, `'SHA-1'`, `'SHA-224'`, `'SHA-256'`, `'SHA-384'`, or `'SHA-512'`.
  If _sign_ is not `False`, the rsa signature of _msg_ is computed using the specified
  hashing algorithm and sent to the remote socket.

* SecureSocket.recv(_channel_=`'\_\_rsa\_\_'`, _decode_=`False`, _timeout_=`-1`)
* SecureSocket.recvRSA(_channel_=`'\_\_rsa\_\_'`, _decode_=`False`, _timeout_=`-1`)
  Waits to receive a message on the _channel_ channel, then decrypts using this socket's private key.
  If _decode_ is true, the decrypted bytes object is decoded into a str object.
  _timeout_ sets the maximum time allowed for any single operation with the remote
  socket (thus the `.recvRSA` method may take longer to complete as a whole).
  If _timeout_ is -1, it defaults to the `SecureSocket`'s default timeout parameter.
  If the remote socket elects to send a message signature (the default), the message will be
  verified against the signature. This will raise `rsa.pkcs1.VerificationError`
  if signature verification fails

### agutil (Main Module)
The following changes have been made to the main `agutil` module:
* `agutil.split_iterable` is now also available as `agutil.clump` which was chosen
as it more clearly describes the function. `agutil.split_iterable` _may_ be removed
in a future release, but this is not yet planned
* Added a function `agutil.splice` which takes a iterable of at least 2 dimensions (M rows by N columns)
and returns an iterable for each column (N iterables of length M).
* `agutil.byteSize` now supports yottabytes
* Added `agutil.context_lock` method, which enforces a timeout when acquiring a native lock
* New exceptions: `agutil.TimeoutExceeded` and `agutil.LockTimeoutExceeded`

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

* agutil.TimeoutExceeded: _(Exception)_

  `OSError` -> `socket.timeout` -> `agutil.TimeoutExceeded`
  This exception is raised by `agutil.ActiveTimeout` when the timeout has expired

* agutil.LockTimeoutExceeded: _(Exception)_

  `OSError` -> `socket.timeout` -> `agutil.TimeoutExceeded` -> `agutil.LockTimeoutExceeded`
  This exception is raised by `agutil.context_lock` when it fails to acquire the
  lock within the provided timeout

* agutil.context_lock(_lock_, _timeout_=`-1`): _(Context Manager)_

  Returns a context manager object. When entering the context it attempts to
  acquire the _lock_. If _timeout_ is a non-negative number, it waits at most
  _timeout_ seconds before raising `agutil.LockTimeoutExceeded`. When exiting
  the context, it always attempts to release the _lock_, regardless of any
  exceptions which may have occurred within the context.

### agutil.ActiveTimeout (new class)
This class has been added to manage a timeout over a set of operations. Specifically,
to enforce that several blocking operations all complete within the given timeout.
The enforcement is not automatic, but relies on checking the timeout when possible

##### API
* ActiveTimeout(_t_): _(Constructor)_

  Constructs a new `agutil.ActiveTimeout` with the specified timeout.
  _t_ should be a positive number indicating an amount of seconds, or `None` if the timeout should not expire.
  This class may be used as a context manager.
  **Note:** This class will not automatically raise timeout exceptions; call `ActiveTimeout.update()` to check if the timeout has expired

* ActiveTimeout.\_\_enter\_\_(): _(Context manager entry)_

  Resets the timer and starts recording time

* ActiveTimeout.\_\_exit\_\_(): _(Context manager exit)_

  Updates the remaining time, but will not raise a timeout exception if the timeout has elapsed.

* ActiveTimeout.update():

  Updates the time remaining. If the timeout has expired, it raises `agutil.TimeoutExceeded`.

* ActiveTimeout.thread_timeout: _(Property)_

  This property always reflects the time remaining in a format useable by the `threading` module.
  It returns the current time remaining, or -1 if the _t_ was None.
  This property may be passed as the timeout to native locks so that
  they will timeout when the ActiveTimeout expires.
  **Note:** This property calls `ActiveTimeout.update()` and will raise `agutil.TimeoutExceeded` if the timout has expired

* ActiveTimeout.socket_timeout: _(Property)_

  This property always reflects the time remaining in a format useable by the `socket` module.
  It returns the current time remaining (including if _t_ was None).
  This property may be passed as the timeout to native sockets or any sockets in the `agutil.io` and `agutil.security` modules so that network operations will timeout when the ActiveTimeout expires.
  **Note:** This property calls `ActiveTimeout.update()` and will raise `agutil.TimeoutExceeded` if the timout has expired

### agutil.status_bar
The following changes have been made to `agutil.status_bar`:
* Added a `passthrough()` method which takes one argument and returns it unchanged
while incrementing the bar by 1.
* Added a _file_ argument to the `status_bar()` constructor

##### API
* status_bar.passthrough(_value_):

  Returns _value_ unchaged, but increments the `status_bar` by 1. Useful for updating
  a bar in list certain comprehensions where `status_bar.iter` is infeasible.

* status_bar(_maximum_, _show\_percent_=`True`, _init_=`True`, _prepend_=`""`, _append_=`""`, _cols_=`int(get\_terminal\_size()[0]/2)`, _update\_threshold_=`.00005`, _debugging_=`False`, _file_=`sys.stdout`) _(constructor)_

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
* IterDispatcher(_func_, \*_args_, _maximum_=`15`, _workertype_=`WORKERTYPE_THREAD`, \*\*_kwargs_): _(constructor)_

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
* DemandDispatcher(_func_, _maximum_=`15`, _workertype_=`WORKERTYPE_THREAD`): _(constructor)_

  Constructs a new `DemandDispatcher`. _func_ is the function to be executed and
  _maximum_ is the maximum number of background workers which can be executed at
  one time. _workertype_ sets the type of workers that will be used (threads or
  processes) and can be any class which follows the Worker interface, but it is
  recommended that you use `ThreadWorker` or `ProcessWorker` (provide the class
  name as the parameter, do not provide a class instance).

### agutil.security (module)
The following changes have been made to the `agutil.security` module:
* Added `configure_cipher`, a utility method for generating a `CipherHeader` based
on settings provided as keyword arguments
* Added `agutil.security.encryptFileObj` and `agutil.security.decryptFileObj`
methods. These methods take the same arguments as `agutil.security.encryptFile`
and `agutil.security.decryptFile` methods except that they take _file-like_ objects
instead of filenames
* Updated cipher used by `agutil-secure`.
  * To Encrypt/Decrypt files in the old format, use the new `-l\--legacy` flag.
* Removed the `-f\--force` flag from `agutil-secure`
* Changed the arguments for `agutil.security.encryptFile`,
`agutil.security.encryptFileObj`, `agutil.security.decryptFile`, and
`agutil.security.decryptFileObj`
* Added the following exceptions:
  * `CipherError`
  * `HeaderError`
  * `HeaderLengthError`
  * `InvalidHeaderError`
  * `EncryptionError`
  * `Decryptionerror`

##### API

* configure_cipher(\*\*_kwargs_):

  Uses keyword arguments to determine cipher configuration and returns a `CipherHeader` reflecting the settings.
  Keyword arguments:
  * `cipher_type`: The AES cipher mode to use. Defaults to EAX.
      Ciphers can be given as the AES.MODE enumeration or a string value
      (Ex: 'EAX' or 9)
  * `secondary_cipher_type`: The AES cipher mode to use for the legacy cipher.
      Cannot be CCM, EAX, GCM, SIV, or OCB. Defaults to CBC
  * `store_nonce`: Stores nonce data in output. If this is disabled, the nonce
      must be communicated separately. Default: True
  * `encrypted_nonce`: Use a legacy cipher to encrypt the primary cipher's nonce.
      Implies `legacy_store_nonce` and not `legacy_randomized_nonce`.
      Default: False
  * `store_tag`: Stores a message tag to verify message authenticity. If this is
      disabled, the validity and integrity of the message cannot be
      guaranteed. Default: True
  * `tag_length`: The length (in bytes) of tne message tag. Default: 16
  * `chunk_length`: The length (in blocks of 256 bytes) of plaintext for each
      chunk. The cipher stream will emit one chunk of ciphertext each time a
      full plaintext chunk is read. Ciphertext and plaintext chunks are not
      necessarily the same size. Default: 16 blocks (4096 bytes)
  * `encrypted_tag`: Use a legacy cipher to encrypt the message authentication
      block. Default: False
  * `enable_streaming`: Configure the cipher to be able to encrypt data as it
      becomes available. Implied value depends on cipher type. If this is
      enabled in conjunction with a cipher that does not support streaming
      (CCM), the entire plaintext must be read in before any output will
      be produced. Default: True
  * `cipher_nonce_length`: Sets the length of the nonce for CTR, CCM, and OCB
      ciphers. Please check the [Pycryptodome](https://pycryptodome.readthedocs.io/en/latest/src/cipher/cipher.html#symmetric-ciphers)
      docs for allowed sizes. For ciphers besides these three, this
      parameter is ignored and a 16-byte nonce is used.
      Default: Largest allowed nonce based on cipher type.
  * `ccm_message_length`: Sets the length of the message for a CCM cipher.
      If this parameter is provided, it will imply `enable_streaming`.
      If streaming is enabled without this parameter, the cipher must read
      the entire plaintext before producing any output.
      Maximum value: 65535
  * `ctr_initial_value`: Sets the initial value of the counter for a CTR cipher.
    Maximum value: 65535. Default: 1.
  * `enable_compatability`: Outputs data in a legacy format compataible with
      older versions of agutil. For compatability with the oldest versions of
      agutil, disable `legacy_validate_nonce`.
      Implies `use_legacy_ciphers` and disables all non-legacy configuration
      options. Default: False
  * `use_legacy_ciphers`: Outputs data in the default modern format, but uses
      a legacy cipher configuration. Required by `enable_compatability`.
      Default: False
  * `legacy_randomized_nonce`: Do not store Nonce or IV in output. Instead, a
      CBC mode cipher will be used and a special data block will be stored
      to allow Decryption without the IV. Exclusive to `legacy_store_nonce`.
      Implies `secondary_cipher_type=CBC` and not `legacy_store_nonce`. Default: False
  * `legacy_store_nonce`: Stores the nonce in plaintext. Exclusive to
        `legacy_randomized_nonce`. If both this and `legacy_randomized_nonce`
        are False, the nonce must be communicated separately. Default: True
  * `legacy_validate_nonce`: Stores data in the EXData block so that the key and
    nonce can be validated during Decryption. Exclusive to `encrypted_nonce`.
    Disable for compatability with the oldest versions of agutil.
    Default: True

* encryptFile(_input\_filename_, _output\_filename_, _key_, _nonce_=`None`, \*\*_kwargs_):

  Opens _input\_filename_ and _output\_filename_ and passes their file handles,
  along with the other arguments, to `encryptFileObj()`. For a description of that
  function, see below.

* encryptFileObj(_reader_, _writer_, _key_, _nonce_=`None`, \*\*_kwargs_):

  Encrypts the data read from _reader_ using the cipher and writes it to _writer_.
  Initializes an `agutil.security.EncryptionCipher` to handle the encryption.
  _kwargs_ are passed to the constructor of the `EncryptionCipher` and may be
  any valid keyword argument to `configure_cipher()` (see above).
  Padding is handled internally (chunks are padded to 16-byte intervals).

* decryptFile(_input\_filename_, _output\_filename_, _key_, _nonce_=`None`, _compatability_=`False`):

  Opens _input\_filename_ and _output\_filename_ and passes their file handles,
  along with the other arguments, to `decryptFileObj()`. For a description of that
  function, see below.

* decryptFileObj(_reader_, _writer_, _key_, _nonce_=`None`, _compatability_=`False`):

  Decrypts the data read from _reader_ using _cipher_ and writes it to _writer_.
  Initializes an `agutil.security.DecryptionCipher` to handle decryption.
  The cipher can handle data encrypted by `agutil` versions between 1.2.0 and 3.1.2.
  _compatability_ must be `True` to decrypt data from earlier versions.

* CipherError: _(Exception)_

  `ValueError` -> `CipherError`
  This is the parent exception type for other cipher errors

* EncryptionError: _(Exception)_

  `ValueError` -> `CipherError` -> `EncryptionError`
  Raised by `agutil.security.EncryptionCipher` if there is an error during encryption

  * DecryptionError: _(Exception)_

    `ValueError` -> `CipherError` -> `DecryptionError`
    Raised by `agutil.security.DecryptionCipher` if there is an error during decryption

* HeaderError: _(Exception)_

  `ValueError` -> `CipherError` -> `HeaderError`
  Raised by ciphers if the header is in an invalid state

* HeaderLengthError: _(Exception)_

  `ValueError` -> `CipherError` -> `HeaderError` -> `HeaderLengthError`
  Raised by `agutil.security.DecryptionCipher` if there was not enough initial data to initialize the cipher

* InvalidHeaderError: _(Exception)_

  `ValueError` -> `CipherError` -> `HeaderError` -> `InvalidHeaderError`
  Raised by ciphers if the header is corrupt or does not specify a valid configuration


### agutil.security.SecureConnection
The following changes have been made to `agutil.security.SecureConnection`:
* This class has been overhauled to be more efficient, and mostly threadless.
* The _retries_ argument of the `send()` function has been removed
* Added a `confirm()` method to await confirmation from the remote socket that a
task has been completed
* Removed the _timeout_ argument from `close()` and `shutdown()`

##### API
* SecureConnection.send(_msg_):

  Sends _msg_ to the remote socket using RSA encryption. The RSA signature of _msg_ is also sent.
  Returns a the task name used to send the _msg_. Use `confirm()` to
  check if the task was a success

* SecureConnection.confirm(_task_, _timeout_=`-1`):

  Waits for confirmation of the _task_ from the remote socket.
  If _timeout_ is a positive number, it waits at most _timeout_ seconds.
  If _timeout_ is `None`, it blocks indefinitely. If _timeout_ is `-1`, it uses the default timeout specified in the constructor.
  Returns `True` or `False` indicating success or failure of the task on the remote end. Raises a `socket.Timeout` exception if the _timeout_ expires.
  Confirmations are sent automatically by the remote socket, but must be `confirm()`-ed manually.
  If a _task_ fails or times out, it is the programmers responsibility to re-attempt the task, if desired.

* SecureConnection.read(_decode_=`True`, _timeout_=`-1`):

  Waits for a message from the remote socket.
  If _timeout_ is a positive number, it waits at most _timeout_ seconds.
  If _timeout_ is `None`, it blocks indefinitely. If _timeout_ is `-1`, it uses the default timeout specified in the constructor.
  Returns `True` or `False` indicating success or failure of the task on the remote end. Raises a `socket.Timeout` exception if the _timeout_ expires.
  If _decode_ is `True`, the message will be decoded to a string when returned

* SecureConnection.sendfile(_filename_):

  Prepares the file specified by _filename_ to be sent and informs the remote socket that the file is available for transfer.
  Starts a background thread which waits for a response from the remote socket before encrypting and sending the file using AES CBC encryption.
  Returns a the task name used to send the file. Use `confirm()` to
  check if the task was a success.

* SecureConnection.savefile(_destination_=`None`, _timeout_=`-1`, _force_=`False`):

  Processes the oldest pending file transfer request or waits at most _timeout_ seconds to receive one.
  If _timeout_ is a positive number, it waits at most _timeout_ seconds.
  If _timeout_ is `None`, it blocks indefinitely. If _timeout_ is `-1`, it uses the default timeout specified in the constructor.
  Returns `True` or `False` indicating success or failure of the task on the remote end. Raises a `socket.Timeout` exception if the _timeout_ expires.
  If _force_ is not `True`, this method will request user confirmation before completing the transfer.
  Once the transfer begins, the socket must receive at least one chunk every _timeout_ seconds or it will raise a `socket.Timeout` exception.
  _destination_ should be the path where the file will be saved.
  If _destination_ is `None`, the file will be saved in the current directory, using the original filename.

* SecureConnection.shutdown():
* SecureConnection.close():

  Closes the underlying socket

### agutil.security.EncryptionCipher (New class)
Added the `EncryptionCipher` class, which is a configurable cipher that provides
the AES encryption backend for `agutil-secure` and the `agutil.security` module.

##### API

* EncryptionCipher(_key_, _nonce_=`None`, _header_=`None`, \*\*_kwargs_): _(Constructor)_

  Constructs a new `EncryptionCipher`. _key_ and _nonce_ are used to initialize the underlying cipher.
  If _nonce_ is `None`, a 16-byte nonce will be automatically generated.
  _header_ should be an `agutil.security.CipherHeader` object to specify the cipher settings.
  If _header_ is `None`, a header will be automatically generated using the provided _kwargs_ (cipher uses default settings if no _kwargs_ are provided).
  See `agutil.security.configure_cipher` for details on different cipher configuration options.
  **Note:** If a _nonce_ was not provided and your configuration disabled storing the nonce,
  you can access the _nonce_ via `EncryptionCipher.nonce`.

* EncryptionCipher.encrypt(_data_):

  Passes the provided _data_ though the internal cipher and returns ciphertext.
  _data_ should be a `Bytes` object.
  This function always returns a `Bytes` object, but the size of the output depends on the length of _data_ and the cipher settings.
  You may call this function as many times as you wish, with any amount of _data_ in each call and any total plaintext size.
  For any given plaintext, calling `encrypt()` on the whole plaintext at once, and calling `encrypt()` on the plaintext in discrete chunks
  will ultimately yield the same ciphertext after calling `finish()`.
  **Note:** Ciphertext is never complete until you call `finish()`

* EncryptionCipher.finish():

  Encrypts any remaining data in the internal buffer and returns final output.
  Complete ciphertext is produced by appending the output from `finish()` to the concatenation of the output from any calls to `encrypt()`.
  In other words, `ciphertext = cipher.encrypt(plaintext) + cipher.finish()`

### agutil.security.DecryptionCipher (New class)
Added the `DecryptionCipher` class, which is a configurable cipher that provides
the AES decryption backend for `agutil-secure` and the `agutil.security` module.

##### API

* DecryptionCipher(_init\_data_, _key_, _nonce_=`None`, _legacy\_force_=`False`): _(Constructor)_

  Initializes a new `DecryptionCipher`.
  _init\_data_ should be the some or all of the ciphertext produced by an `EncryptionCipher`.
  _init\_data_ is used to determine cipher configuration and any unused data is buffered until calling `decrypt()`.
  _init\_data_ needs to be at least 16 bytes, but depending on the inferred configuration, it may need to be longer to properly initialize the cipher.
  The constructor will raise an `agutil.security.HeaderLengthError` if _init\_data_ was too short.
  64 bytes is almost always enough data to initialize the cipher.
  If the constructor fails due to _init\_data_ length, try again with more data.
  _key_ and _nonce_ are used to initialize the underlying cipher.
  If _nonce_ is `None`, the cipher expects to find a _nonce_ in the header data.
  If the header appears invalid, the `DecryptionCipher` assumes that the input is in legacy (headerless) format and attempts to continue initialization.
  Files encrypted by `agutil-secure` 1.2.0 through 3.1.2 can be handled silently.
  Files encrypted by `agutil-secure` 1.1.3 and earlier require _legacy\_force_ to be `True`

* DecryptionCipher.decrypt(_data_=`b''`):

  Decrypts the provided ciphertext. _data_ should be a `Bytes` object.
  This function always returns a `Bytes` object, but the size of the output depends on the length of _data_ and the cipher settings.
  You may call this function as many times as you wish, with any amount of _data_ in each call and any total ciphertext size.
  For any given cipher, calling `decrypt()` on the whole ciphertext at once, and calling `decrypt()` on the ciphertext in discrete chunks
  will ultimately yield the same plaintext after calling `finish()`.
  **Note:** Plaintext is never complete until you call `finish()`

* DecryptionCipher.finish():

  Decrypts any remaining data in the internal buffer and returns final output.
  Complete plaintext is produced by appending the output from `finish()` to the concatenation of the output from any calls to `decrypt()`.
  In other words, `plaintext = cipher.decrypt(ciphertext) + cipher.finish()`

### agutil.security.CipherHeader (New class)
Added the `CipherHeader` class, which stores the configuration of an `EncryptionCipher` or `DecryptionCipher`
and can be used to produce the 16-byte cipher header representing the configuration

##### API

* CipherHeader(_header_=`None`): _(Constructor)_

  Creates a new `CipherHeader`.
  _header_ should be a **15-byte** long `Bytes` object (excludes final hamming weight byte)
  representing a cipher configuration.
  If _header_ is `None`, a blank header is produced.
  **Note:** The default (blank) header is valid in the sense that it follows the
  cipher header format, but it is not suitable for immediate use in a cipher.
  After initializing a blank header, you must set its attributes into a valid
  cipher configuration.

* CipherHeader.valid: _(Property, readonly)_

  Returns `True` if the header is in a valid state. `False` otherwise

* CipherHeader.weight: _(Property, readonly)_

  Returns the hamming weight of the header

* CipherHeader.data: _(Property, readonly)_

  Returns the **16-byte** representation of this header

* CipherHeader.legacy_bitmask: _(Property)_

  Returns a `Bitmask` object containing the state of the legacy cipher bitmask.
  You may also assign a `Bitmask` object to this property to overwrite the bitmask

* CipherHeader.control_bitmask: _(Property)_

  Returns a `Bitmask` object containing the state of the main cipher bitmask.
  You may also assign a `Bitmask` object to this property to overwrite the bitmask

* CipherHeader.exdata_size: _(Property)_

  Returns the size (in bytes) of the extra data block.
  You may also assign an integer (maximum 255) to this property

* CipherHeader.cipher_id: _(Property)_

  Returns the ID of the primary cipher.
  You may also assign an integer (maximum 255) to this property

* CipherHeader.secondary_id: _(Property)_

  Returns the ID of the legacy cipher.
  You may also assign an integer (maximum 255) to this property

* CipherHeader.cipher_data: _(Property)_

  Returns the 6-byte cipher_data segment as a `Bytes` object.
  You may also assign a 6-byte `Bytes` object to this property

* CipherHeader.use_modern_cipher: _(Property, readonly)_

  Returns `True` if the current header configuration would enable the use of
  the primary (modern) cipher.

### agutil.security.Bitmask (New class)
Added the `Bitmask` class to allow reading and manipulating a single-byte bitmask
using pythons `[]` indexing API. This class uses an `agutil.search_range` to perform
underlying bit manipulations and queries

##### API

* Bitmask(_n_=`0`, _values_=`None`): _(Constructor)_

  Constructs a new `Bitmask`.
  _n_ should represent the integer value of the bitmask to start from.
  `0` is an empty mask with no bits set.
  Alternatively, _values_ may be a list of 8 boolean values to initialize
  the bitmask.

* Bitmask.\_\_getitem\_\_(_i_):

  Gets the value of bit _i_ (Big Endian).

* Bitmask.\_\_setitem\_\_(_i_, _v_):

  Sets the value of bit _i_ (Big Endian).
  If _v_ evaluates to `False`, the bit is un-set instead

* Bitmask.set_range(_start_, _stop_, _value_=`True`):

  Sets the bits in the range [_start_, _stop_).
  If _value_ evaluates to `False`, the bits are un-set instead.
