# agutil
* Master build status: [![Master Build Status](https://travis-ci.org/agraubert/agutil.svg?branch=master)](https://travis-ci.org/agraubert/agutil) [![Live Package Version](https://img.shields.io/pypi/v/agutil.svg)](https://pypi.python.org/pypi/agutil)
* Development build status: [![Dev Build Status](https://travis-ci.org/agraubert/agutil.svg?branch=dev)](https://travis-ci.org/agraubert/agutil) [![Dev Coverage Status](https://coveralls.io/repos/github/agraubert/agutil/badge.svg?branch=dev)](https://coveralls.io/github/agraubert/agutil?branch=dev)

A collection of python utilities

__Version:__ 0.5.0b

###### Tools:
* search_range (A utility for manipulating numerical ranges)
* status_bar (A simple progress bar indicator)
* Logger (A class for fast, simple, logging)
* Several standalone utility methods (See the [agutil module page](https://github.com/agraubert/agutil/wiki) on the wiki)


The __bio__ package:
* maf2bed (A command line utility for parsing a .maf file and converting coordinates from 1-based (maf standard) to 0-based (bed standard))
* tsvmanip (A command line utility for filtering, rearranging, and modifying tsv files)

The __io__ package:
* Socket (A low-level network IO class built on top of the standard socket class)
* SocketServer (A low-level listen server to accept connections and return Socket classes)
* QueuedSocket (A low-level network IO class built to manage input across multiple channels)
* parseIdentifier and checkIdentifier (Utility methods for parsing and verifying protocol identifiers)

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

##Features in Development:

##LOGGER
The `agutil` module includes the `Logger` class, which provides a simple interface for quick logging.  Messages can be logged over specific channels, and each channel can be set to log to a file, stdout, neither, or both.  The actual `Logger` instance is meant to be the point of control for the log.  All `agutil` classes which support logging will log messages through the lambda returned by `Logger.bindToSender()`.

Note: `agutil` also includes `DummyLog`, a default log used in other `agutil` classes which does no actual logging or printing

#####API
* Logger(filename, header="Agutil Logger", log_level=LOGLEVEL_INFO, stdout_level=LOGLEVEL_NONE) _(constructor)_
  Constructs a new `Logger` instance.  If _filename_ is not None, it is taken to be the filename the logger should use for its file log.
  _header_ is a simple description of what is being logged, and is printed to the top of the log.  _log\_level_ sets the minimum allowed channel for messages being logged (see: [Default Channels](#default-channels)).  _stdout\_level_ sets the minimum allowed channel for message to be printed to stdout as they're logged (see: [Default Channels](#default-channels)).

* Logger.log(message, sender="ANONYMOUS", channel="INFO")
  Queues the message _message_ to be logged.  _sender_ and _channel_ convey additional information regarding what is logging the message and why, and are also used to determine if and where the message is logged.

* Logger.close()
  Immediately stops accepting new messages to log, and waits up to 1 second for the logger background thread to finish processing its backlog of messages and perform other shutdown tasks

* Logger.bindToSender(sender, can_close=True)
  Binds _sender_ to the _sender_ argument of `Logger.log()` and returns the bound function, with some additional connections to the `Logger` (such as the ability to generate new bound methods for subordinates, or to close the log).
  _can\_close_ controls whether or not the returned lambda has the capacity to close the log.  By default, `Logger.bindToSender()` returns bound methods which can close the log, but subordinate bound methods returned by the original cannot.  The intent is that many different classes (some embedded or extended) can share the same `Logger` object, but only the top level objects will actually close the log.  In addition to calling the returned method, the function returned by `bindToSender()` also has a `.name` attribute (which is set to the _sender_ argument), a `.close()` method (which will close the `Logger` it's attached to iff _can\_close_ was True), and a `.bindToSender()` method (identical to this one, except that _can\_close_ will always be False and cannot be overridden).

* Logger.setChannelFilters(channel, log, display)
  Sets the filters for the specified _channel_.  If _channel_ is not registered (only the 5 default channels are registered by the constructor) it becomes registered and capable of logging.  Iff _log_ is True, then messages in _channel_ will be logged to the log file.  Iff _display_ is True, messages in _channel_ will be printed to stdout.

* Logger.setChannelCollection(channel, collect)
  Sets collection on _channel_.  Channels with collection enabled will record a copy of all messages logged, and dump a copy at the end of the log, when `Logger.close()` is called (messages are also logged normally in the body of the log).  By default only 'ERROR' and 'WARN' have collection enabled.  If _collect_ is True, then collection is enabled for _channel_.  If _collect_ is False, collection is disabled (clearing out any collected messages from this channel if collection was previously enabled)

* Logger.mute(mutee, muter="ANONYMOUS")
  Suppresses any messages from _mutee_ until `Logger.unmute()` is called.

* Logger.unmute(mutee)
  Unmutes the sender _mutee_.  A maximum of 1 message from _mutee_ sent while muting was enabled will be displayed.

#####Default Channels
In addition to supporting any user-created channels, the `Logger` class supports 5 built-in channels:
* ERROR: For logging errors and exceptions
* WARN: For logging warnings or minor errors
* INFO: For logging informative, and human-readable information
* DEBUG: For logging messages useful to debugging
* DETAIL: For logging extremely detailed information regarding program function

Each channel also has a constant set at the class level to use as input for the constructor's log\_level and stdout\_level arguments:
* LOGLEVEL_ERROR: Logs/prints only errors
* LOGLEVEL_WARN: Logs/prints errors and warnings
* LOGLEVEL_INFO: Logs/prints errors, warnings, and info
* LOGLEVEL_DEBUG: Logs/prints errors, warnings, info, and debug info
* LOGLEVEL_DETAIL: Logs/prints all messages to the 5 standard channels

And the additional level:
* LOGLEVEL_NONE: Do not log or print any messages to the 5 standard channels

##STATUS_BAR
The following change has been made to the `agutil.status_bar` api:
The _transcript_ parameter has been removed from the constructor.  The status_bar no longer supports logging a transcript of activity.

#####API
* status_bar(maximum, show_percent = False, init=True, prepend="", append="", cols=int(get_terminal_size()[0]/2), update_threshold=.00005, debugging=False _(constructor)_
  Creates a new status_bar instance ranging from 0 to _maximum_

  _show\_percent_ toggles whether or not a percentage meter should be displayed to the right of the bar

  _init_ sets whether or not the status_bar should immediately display.  If set to false, the bar is displayed at the first update

  _prepend_ is text to be prepended to the left of the bar.  It will always remain to the left of the bar as the display updates.  **WARNING** Prepended text offsets the bar.  If any part of the bar (including prepended or appended text) extends beyond a single line on the console, the status bar will not display properly.  Prepended text should be kept short

  _append_ is text to be appended to the right of the bar.  It will always remain to the right of the bar as the display updates.  **WARNING** Appended text extends the display.  If any part of the bar (including prepended or appended text) extends beyond a single line of the console, the status bar will not display properly.  Appended text should be kept short

  _cols_ sets how long the bar should be.  It defaults to half the terminal size

  _update\_threshold_ sets the minimum change in percentage to trigger an update to the percentage meter

  _debugging_ triggers the status_bar to never print to stdout.  If set true, no output will be produced, but exact string of what *would* be displayed is maintained at all times in the _display_ attribute

##io.QUEUEDSOCKET
The following changes have been made to the `agutil.io.QueuedSocket` API:
A _logmethod_ parameter has been added to the constructor
An _upstreamIdentifier_ parameter has been added to the constructor

#####API
* QueuedSocket(socket, upstreamIdentifier=_PROTOCOL_IDENTIFIER_, logmethod=DummyLog) _(constructor)_
  Takes an `agutil.io.Socket` class to extend.  _upstreamIdentifier_ allows subclasses or wrapper classes to provide their own identifier tags for confirming protocols at each layer.  _logmethod_ specifies a logging object to use.  It defaults to `agutil.DummyLog` (which does not log anything).  _logmethod_ may either be an `agutil.Logger` class, or a bound method returned by `agutil.Logger.bindToSender()`.

##security.SECURECONNECTION
The following changes have been made to the `agutil.security.SecureConnection` API:
A _logmethod_ parameter has been added to the constructor, and the _verbose_ parameter has been removed
An _upstreamIdentifier_ parameter has been added to the constructor

#####API
* SecureConnection(address, port, password=None, rsabits=4096, timeout=3, upstreamIdentifier=_PROTOCOL_IDENTIFIER_, logmethod=DummyLog) _(constructor)_
  Opens a new secure connection to the address specified by opening a new `SecureSocket` to use internally.
  If _address_ is set to '' or 'listen', the `SecureConnection` will listen for an incoming connection on _port_.
  Otherwise, it attempts to connect to another `SecureConnection` on the specified _port_ at _address_.
  _password_ and _rsabits_ configure the internal `SecureSocket`, and are used for its constructor.
  _timeout_ sets the default timeout on the internal `SecureSocket`.
  _upstreamIdentifier_ allows subclasses or wrapper classes to provide their own identifier tags for confirming protocols at each layer.
  _logmethod_ specifies a logging object to use.  It defaults to `agutil.DummyLog` (which does not log anything).  _logmethod_ may either be an `agutil.Logger` class, or a bound method returned by `agutil.Logger.bindToSender()`.


##security.SECURESOCKET
The following changes have been made to the `agutil.security.SecureSocket` API:
A _logmethod_ parameter has been added to the constructor, and the _verbose_ parameter has been removed
An _upstreamIdentifier_ parameter has been added to the constructor

#####API
* SecureSocket(socket, password=None, rsabits=4096, timeout=3, upstreamIdentifier=_PROTOCOL_IDENTIFIER_, logmethod=DummyLog) _(constructor)_
  Initializes an `agutil.security.SecureSocket` object around an `agutil.io.Socket` instance.
  Generates a new RSA keypair of _rsabits_ size, and exchanges public keys with the remote socket (which must also be a `SecureSocket`).
  If _password_ is set, and not None, it is used to generate an AES ECB cipher which is used to encrypt all basic communications between the sockets (the remote socket must use the same password).
  _timeout_ sets the default timeout for receiving incoming messages.
  _upstreamIdentifier_ allows subclasses or wrapper classes to provide their own identifier tags for confirming protocols at each layer.
  _logmethod_ specifies a logging object to use.  It defaults to `agutil.DummyLog` (which does not log anything).  _logmethod_ may either be an `agutil.Logger` class, or a bound method returned by `agutil.Logger.bindToSender()`.


##security.SECURESERVER
The following change has been made to the `agutil.security.SecureServer` API:
A _logmethod_ parameter has been added to the constructor, and the _childverbose_ parameter has been removed

#####API:
* SecureServer(port, address='', queue=3, password=None, rsabits=4096, childtimeout=3, childlogger=DummyLog) _(constructor)_
  Binds to _port_ and accepts new connections. _port_, _address_, and _queue_ work identically to `agutil.io.SocketServer` (as the `SecureServer` uses a `SocketServer` internally).  _password_, _rsabits_, _childtimeout_, and _childlogger_  set the _password_, _rsabits_, _timeout_, and _logmethod_ arguments (respectively) to the `SecureConnection` constructor for each accepted connection.
  _childlogger_ defaults to `agutil.DummyLog` (which does not log anything).  _childlogger_ may either be an `agutil.Logger` class, or a bound method returned by `agutil.Logger.bindToSender()`.

##security.AGUTIL-SECURE
The `agutil.security` module provides a command line interface for encrypting and decrypting files.

#####COMMAND USAGE
* `$ agutil-secure {encrypt, decrypt} input output password [--py33] [-h]`
  Reads from _input_ and either encrypts or decrypts data before writing to _output_.  Note that files encrypted on python 3.3, or using the _--py33_ flag, can only be decrypted on 3.3 (or with the flag) and visa-versa.

  positional arguments:

  _{encrypt,decrypt}_  Sets the mode to either encryption or decryption

  _input_              Input file to encrypt or decrypt

  _output_             Where to save the encrypted or decrypted file

  _password_           The password to encrypt or decrypt with. Note: passwords containing (spaces) must be encapsulated with quotations ("")

  optional arguments:

    _-h, --help_         show this help message and exit

    _--py33_             Forces encryption or decryption to use the simplified, 3.3 compatable pbkdf2_hmac

##agutil utility methods
* agutil.intToBytes(num, padding\_length=0)
  Converts the int _num_ to its big-endian byte representation.  If the length of the converted bytestring is less than _padding\_length_, 0-bytes (`\x00`) are added to the beginning of the string.  This has to do with an inherent issue with int<->byte conversion: 0-bytes in more-significant end of a bytestring are equivalent to adding zeroes to the left of an integer.  These bytes are lost in a conversion from bytes->int.  _padding\_length_ provides a solution if the length of the original bytestring is known.  For conversions of int->bytes->int, the _padding\_length_ parameter is not needed.  For conversions of bytes->int->bytes, it may be necessary to either communicate the desired length in advance, or prepend a non-zero byte to the start of the string

* agutil.bytesToInt(num)
  Converts the byte sequence _num_ into an integer

* agutil.byte_xor(b1, b2)
  Returns a byte sequence equivalent to the XOR of each byte in _b1_ with the corresponding byte in _b2_

* agutil.split_iterable(seq, length)
  Yields iterables which take from _seq_ in chunks up to _length_.  Each iterable returned will yield up to _length_ items.  If chained together, the iterables returned would iterate the same sequence as _seq_.

##io.SOCKET
The following changes have been made to the `agutil.io.Socket` API:
An _upstreamIdentifier_ parameter has been added to the constructor

#####API
* Socket(address, port, upstreamIdentifier=_PROTOCOL_IDENTIFIER_) _(constructor)_
  Creates a connection to _address_:_port_.
  _upstreamIdentifier_ allows subclasses or wrapper classes to provide their own identifier tags for confirming protocols at each layer.

##io.PARSEIDENTIFIER and io.CHECKIDENTIFIER
The `agutil.io` module includes two methods for working with agutil's protocol identifier scheme: `agutil.io.parseIdentifier()` and `agutil.io.checkIdentifier()`.

#####API
* parseIdentifier(identifier)
  Parses the string _identifier_ into a dictionary of tag:value pairs. _identifier_ must be a string made up of one or more valid concatenated agutil protocol tags in the following form: `<tagname>` or `<tagname:value>`.
  Example for an `agutil.io.QueuedSocket` identifier: `<agutil><__protocol__:1.0.0><agutil.io.queuedsocket:1.0.0><agutil.io.socket:1.0.0>`.
  Tags without a specified value (ie: `<agutil>`) are mapped to True in the returned dictonary

* checkIdentifier(identifier, key, value=True)
  Checks that _key_ exists in the dictionary _identifier_ and that _identifier[key]_ == _value_
  Returns False if at least one of those conditions is not true
