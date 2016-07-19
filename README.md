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
* SecureSocket (A mid-level network IO class built to manage encrypted network communications)
* SecureConnection (A high-level, multithreaded class for sending and receiving encrypted files and messages)
* SecureServer (A low-level listen server to accept connections and return SecureConnection instances)
* encryptFile and decryptFile (Simple methods for encrypting and decrypting local files)

##Documentation:
Detailed documentation of these packages can be found on the [agutil Github wiki page](https://github.com/agraubert/agutil/wiki)

##Installation note:
This package requires PyCrypto, which typically has issues compiling on windows.  If you are on windows and `pip install agutil` fails during the installation of PyCrypto, then follow the instructions [here](https://github.com/sfbahr/PyCrypto-Wheels) for installing PyCrypto from a precompiled wheel, and then run `pip install agutil` again.

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


##security.SECURESOCKET
The following change has been made to the `agutil.security.SecureSocket` API:

The previous `agutl.security.SecureSocket` class has been removed and replaced with a completely overhauled class.  For a class similar to the old `SecureSocket` see: `SecureConnection`.

The `agutil.security` module includes the `SecureSocket` class, which wraps over an `agutil.io.Socket` instance.
A `SecureSocket` class allows for encrypted communications using RSA or AES encryption.

#####API
* SecureSocket(socket, password=None, rsabits=4096, verbose=False, timeout=3) _(constructor)_
  Initializes an `agutil.security.SecureSocket` object around an `agutil.io.Socket` instance.
  Generates a new RSA keypair of _rsabits_ size, and exchanges public keys with the remote socket (which must also be a `SecureSocket`).
  If _password_ is set, and not None, it is used to generate an AES ECB cipher which is used to encrypt all basic communications between the sockets (the remote socket must use the same password).
  If _verbose_ is True, the `SecureSocket` will print verbose messages regarding the activity through the socket
  _timeout_ sets the default timeout for receiving incoming messages.

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


##security.SECURECONNECTION
The `agutil.security` module includes the `SecureConnection` class which provides a high-level interface for sending and receiving secure messages and files.  All tasks are run in background threads, each exchanging data over a different channel on the underlying SecureSocket, allowing for many simultaneous tasks to be run.

#####API
* SecureConnection(address, port, password=None, rsabits=4096, verbose=False, timeout=3) _(constructor)_
  Opens a new secure connection to the address specified by opening a new `SecureSocket` to use internally.
  If _address_ is set to '' or 'listen', the `SecureConnection` will listen for an incoming connection on _port_.
  Otherwise, it attempts to connect to another `SecureConnection` on the specified _port_ at _address_.
  _password_ and _rsabits_ configure the internal `SecureSocket`, and are used for its constructor.
  _verbose_ sets the `SecureConnection` and its internal components to print verbose messages.
  _timeout_ sets the default timeout on the internal `SecureSocket`

* SecureConnection.send(msg, retries=1)
  Starts a background task to send _msg_ to the remote socket using RSA encryption.  _retries_ sets the number of attempts that will be made to send _msg_ if the remote socket fails to reconstruct and decrypt the message

* SecureConnection.read(decode=True, timeout=None)
  Returns the oldest unread message received, or waits until a message is received.  If _decode_ is True, the received bytes object is decoded into a str object before returning.  If _timeout_ is not None, this is the maximum amount of time, in seconds, to wait for an incoming message (raises a socket.timeout exception if no message is received in time).  If _timeout_ is None, `read()` will block indefinitely until a message is received

* SecureConnection.sendfile(filename)
  Starts a background task to send the file specified by the path _filename_.  The file is not immediately sent, however.  The remote socket is sent a request for a file transfer.  The transfer is initiated when the remote socket approves the transfer with `savefile()`.  Because of this, the file should not be deleted until after the transfer is known to be completed. Files are sent and encrypted using an AES CBC cipher with a new randomized 32-byte key for each transfer (the key is exchanged using RSA).

* SecureConnection.savefile(destination, timeout=None, force=False)
  Processes the oldest pending file transfer request or waits up to _timeout_ seconds to receive a request.  If _force_ is True, the request is automatically accepted, otherwise the user is prompted to accept or deny the request.  If the request is accepted (either by _force_ or manual acceptance) it is decrypted and saved to _destination_

* SecureConnection.shutdown(timeout=3)
* SecureConnection.close(timeout=3)
  Closes the connection.  The `SecureConnection` immediately stops accepting new commands from both the user and the remote socket (but currently queued or running tasks are allowed to queue new tasks).  Waits up to _timeout_ seconds for all currently runnning tasks to complete.  Then (regardless of if all tasks completed or not) it prevents any new tasks from being queued.  Lastly, the internal `SecureSocket` connection is closed.


##security.SECURESERVER
The `agutil.security` module includes the `SecureServer` class, which is similar to the `agutil.io.SocketServer` class, but it returns `SecureConnection` instances instead of `Socket` instances.

#####API
* SecureServer(port, address='', queue=3, password=None, rsabits=4096, childverbose=False, childtimeout=3) _(constructor)_
  Binds to _port_ and accepts new connections. _port_, _address_, and _queue_ work identically to `agutil.io.SocketServer` (as the `SecureServer` uses a `SocketServer` internally).  _password_, _rsabits_, _childverbose_, and _childtimeout_ set the _password_, _rsabits_, _verbose_, and _timeout_ arguments (respectively) to the `SecureConnection` constructor for each accepted connection.

* SecureServer.accept()
  Waits for a connection and returns a new `SecureConnection`

* SecureServer.close()
  Closes the underlying `SocketServer`
  

##security.ENCRYPTFILE security.DECRYPTFILE
The `agutil.security` module includes two methods for file encryption and decryption: `encryptFile()` and `decryptFile()`.

#####API
* encryptFile(input\_filename, output\_filename, cipher)
  Encrypts the file specified by _input\_filename_ and saves it to _output\_filename_ using _cipher_.
  The cipher is not required to be any class, but it must support an `encrypt()` method, which takes a chunk of text, and returns a ciphered chunk.  Padding is handled internally (chunks are padded to 16-byte intervals).

* decryptFile(input_filename, output_filename, cipher)
  Decrypts the file specified by _input\_filename_ and saves it to _output\_filename_ using _cipher_.
  The cipher is not required to be any class, but it must support an `decrypt()` method, which takes a chunk of ciphertext, and returns a deciphered chunk.  Unpadding is handled internally (chunks are padded to 16-byte intervals).
