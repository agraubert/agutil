# agutil
* Master build status: [![Master Build Status](https://travis-ci.org/agraubert/agutil.svg?branch=master)](https://travis-ci.org/agraubert/agutil)
* Development build status: [![Dev Build Status](https://travis-ci.org/agraubert/agutil.svg?branch=dev)](https://travis-ci.org/agraubert/agutil)

A collection of python utilities

__Version:__ 0.4.1b

###### Tools:
* search_range (A utility for manipulating numerical ranges)
* status_bar (A simple progress bar indicator)


The __bio__ package:
* maf2bed (A command line utility for parsing a .maf file and converting coordinates from 1-based (maf standard) to 0-based (bed standard))
* tsvmanip (A command line utility for filtering, rearranging, and modifying tsv files)

The __io__ package:
* Socket (A low-level network IO class built on top of the standard socket class)
* SocketServer (A low-level listen server to accept connections and return Socket classes)
* QueuedSocket (A low-level network IO class built to manage input across multiple channels)

The __security__ package:
* SecureSocket (A basic network IO system for exchanging files and text securely)

##Documentation:
Detailed documentation of these packages can be found on the [agutil Github wiki page](https://github.com/agraubert/agutil/wiki)

##Features in development:

##io.QUEUEDSOCKET
The `agutil.io` module includes the class `QueuedSocket` which wraps a regular `agutil.io.Socket` class.
`QueuedSocket` instances are designed to allow multiple threads to utilize the same socket by dividing data across multiple channels.
The `.send()` and `.recv()` methods now take an (optional) additional _channel_ argument compared to the methods on a regular `agutil.io.Socket` instance (API below).  `.send()` and `.recv()` will send and receive data across the specified channel.

#####API
* QueuedSocket(socket) _(constructor)_
  Takes an `agutil.io.Socket` class to extend.

* QueuedSocket.send(msg, channel='\_\_orphan\_\_')
  Sends a message over the specified _channel_.  If the _channel_ argument is omitted, it is sent over a default channel.

* QueuedSocket.recv(channel='\_\_orphan\_\_', decode=False, timeout=None)
  Receives a message from the specified _channel_, or blocks until a message is available.  If _decode_ is True, the bytes object is decoded into a str object. If a timeout is specified and not None, the method will block for at most _timeout_ seconds, then raise a `socket.timeout` exception.

* QueuedSocket.close(timeout=1)
  Shuts down the connection and closes the underlying `agutil.io.Socket`.  If a timeout is specified, this is the maximum amount of time the QueuedSocket will wait for its background thread to finish before closing the socket.

* QueuedSocket.settimeout(timeout)
  Sets the socket timeout.  This method is identical to `agutil.io.Socket.settimeout()`

* QueuedSocket.gettimeout()
  Returns the current timeout.  This method is identical to `agutil.io.Socket.gettimeout()`
  

##io.SOCKET
The following change has been made to the `agutil.io.Socket` API:

#####API
* Socket.gettimeout()
  Returns the timeout set on the underlying socket
