# agutil
* Master build status: [![Master Build Status](https://travis-ci.org/agraubert/agutil.svg?branch=master)](https://travis-ci.org/agraubert/agutil) [![Master Coverage Status](https://coveralls.io/repos/github/agraubert/agutil/badge.svg?branch=master)](https://coveralls.io/github/agraubert/agutil?branch=master)
* Development build status: [![Dev Build Status](https://travis-ci.org/agraubert/agutil.svg?branch=dev)](https://travis-ci.org/agraubert/agutil) [![Dev Coverage Status](https://coveralls.io/repos/github/agraubert/agutil/badge.svg?branch=dev)](https://coveralls.io/github/agraubert/agutil?branch=dev)

A collection of python utilities

__Version:__ 0.5.0b

###### Tools:
* search_range (A utility for manipulating numerical ranges)
* status_bar (A simple progress bar indicator)
* Logger (A class for fast, simple, logging)


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

##Documentation:
Detailed documentation of these packages can be found on the [agutil Github wiki page](https://github.com/agraubert/agutil/wiki)

##Installation note:
This package requires PyCrypto, which typically has issues compiling on windows.  If you are on windows and `pip install agutil` fails during the installation of PyCrypto, then follow the instructions [here](https://github.com/sfbahr/PyCrypto-Wheels) for installing PyCrypto from a precompiled wheel, and then run `pip install agutil` again.

##Features in Development:

##agutil.LOGGER
The `agutil` module includes the `Logger` class, which provides a simple interface for quick logging.  Messages can be logged over specific channels, and each channel can be set to log to a file, stdout, neither, or both.

#####API
* Logger(filename, header="Agutil Logger", log_level=LOGLEVEL_INFO, stdout_level=LOGLEVEL_NONE) _(constructor)_
  Constructs a new `Logger` instance.  If _filename_ is not None, it is taken to be the filename the logger should use for its file log.
  _header_ is a simple description of what is being logged, and is printed to the top of the log.  _log\_level_ sets the minimum allowed channel for messages being logged (see: [Default Channels](#default-channels)).  _stdout\_level_ sets the minimum allowed channel for message to be printed to stdout as they're logged (see: [Default Channels](#default-channels)).

* Logger.log(message, sender="ANONYMOUS", channel="INFO")
  Queues the message _message_ to be logged.  _sender_ and _channel_ convey additional information regarding what is logging the message and why, and are also used to determine if and where the message is logged.

* Logger.close()
  Immediately stops accepting new messages to log, and waits up to 1 second for the logger background thread to finish processing its backlog of messages and perform other shutdown tasks

* Logger.bindToSender(sender)
  Returns a binds _sender_ to the _sender_ argument of `Logger.log()` and returns the bound function.  `Logger.bindToSender('foo')('message', 'channel')` is equivalent to `Logger.log('message', 'foo', 'channel')`

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
