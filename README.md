# agutil
* Master build status: [![Master Build Status](https://travis-ci.org/agraubert/agutil.svg?branch=master)](https://travis-ci.org/agraubert/agutil)
* Development build status: [![Dev Build Status](https://travis-ci.org/agraubert/agutil.svg?branch=dev)](https://travis-ci.org/agraubert/agutil)

A collection of python utilities

__Version:__ 0.4.0b

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

The following change has been made to the `agutil.security.SecureSocket` api:

The `agutil.security` includes the `SecureSocket` class, which allows for secure bidirectional communication.
`agutil.security.new()` can be used as an alias to construct a SecureSocket

#####API
* SecureSocket(self, address, port, initPassword=None, defaultbits=4096, verbose=False, console=False) _(constructor)_
  Creates a new `SecureSocket` connection.  If _address_ is '' or 'listen', it will listen for an incoming connection instead of attempting to connect to a remote socket.  _password_ is optional, and disabled by default.  If set, it is used to generate an AES cipher which is used for the exchange of the initial encryption keys.  If _password_ is set, both sockets must set the same password to connect.  _defaultbits_ sets the default size of rsa keys for new channels.  The default text channel (which is opened automatically during the establishment of a connection) is set using the connecting socket's _defaultbits_ setting (not the listening socket's).  _verbose_ is a flag which enables some output from sockets during their operation

#####security.SECURESOCKET API
* SecureSocket.new\_channel(self, name, rsabits=-1, mode='text')
  Opens a new channel to the remote socket named _name_.  The _rsabits_ parameter can be used to override the length of the rsa key for this channel, but if not set (or -1) it defaults to the _defaultbits_ parameter used in construction.  The _mode_ parameter sets the channel mode (currently only 'text' and 'files' channels are supported)

* SecureSocket.close\_channel(self, name)
  Closes the channel _name_

* SecureSocket.disconnect(self, notify=True)
* SecureSocket.close()
* SecureSocket.__del__() _(Deconstructor)_
  Terminates the connection to the remote socket

* SecureSocket.send(self, payload, channel="\_default\_")
  Send text or files to the remote socket.  Defaults to sending text over the "\_default\_" channel, but the _channel_ parameter can override which channel _payload_ is sent over.  If the channel is a text channel, _payload_ is encrypted using that channel's rsa key, and sent.  If the channel is a file channel, _payload_ is taken to be the source filepath.  A randomized AES cipher is used to encrypt the file before sending, and the channel's rsa key is used to encrypt and send the AES key to decrypt the file.

* SecureSocket.sendfile(self, filepath, channel="\_default\_file\_")
  Convienience method for sending a file.  Defaults to sending files over the "\_default\_file\_" channel (opens the channel if it doesn't exist yet).

* SecureSocket.read(self, channel="\_default\_")
  Decrypts and returns the oldest unread message in _channel_.

* SecureSocket.savefile(self, filepath, channel="\_default\_file\_")
  Decrypts and saves the oldest unsaved file in _channel_, and saves to _filepath_


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


The following change has been made to the `agutil.io.Socket` API:

#####API
* Socket.gettimeout()
  Returns the timeout set on the underlying socket
