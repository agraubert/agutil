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

The __security__ package:
* SecureSocket (A basic network IO system for exchanging files and text securely)

##Documentation:
Detailed documentation of these packages can be found on the [agutil Github wiki page](https://github.com/agraubert/agutil/wiki)

##Features in development:

##security.NEW (method)
The `agutil.security` module includes the `new()` method, which is a wrapper for the `SecureSocket` constructor.
`new()` can be used to construct both ends of a `SecureSocket` connection, without the need for two methods with different API's.
`new()` is the preferred method for constructing a `SecureSocket`, and so the actual constructor will not be documented

#####API
* new(address, port, password=None, defaultbits=4096, verbose=False)
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
