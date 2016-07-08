# agutil
* Master build status: [![Master Build Status](https://travis-ci.org/agraubert/agutil.svg?branch=master)](https://travis-ci.org/agraubert/agutil)
* Development build status: [![Dev Build Status](https://travis-ci.org/agraubert/agutil.svg?branch=dev)](https://travis-ci.org/agraubert/agutil)

A collection of python utilities

__Version:__ 0.3.0a

###### Tools:
* search_range (A utility for manipulating numerical ranges)
* status_bar (A simple progress bar indicator)


The __bio__ package:
* maf2bed (A command line utility for parsing a .maf file and converting coordinates from 1-based (maf standard) to 0-based (bed standard))
* tsvmanip (A command line utility for filtering, rearranging, and modifying tsv files)

The __io__ package:
* Socket (A low-level network IO class built on top of the standard socket class)
* QueuedSocket (An IO class built on top of the agutil.io.Socket class.  Performs IO on a background thread and exchanges data with other threads through queues)
* SocketServer (A low-level listen server to accept connections and return Socket classes)

##Documentation:
Detailed documentation of these packages can be found on the [agutil Github wiki page](https://github.com/agraubert/agutil/wiki)

##Features in development:

##io.QUEUEDSOCKET
The `agutil.io` module includes the `QueuedSocket` class, which operates similarly to the `Socket` class,
except that IO is constantly performed on a background thread.  The send() and recv() methods enqueue data for transmission
or dequeue received data, respectively

##API
* QueuedSocket(\_socket): _(constructor)_
  Wraps a QueuedSocket around an already connected `agutil.io.Socket` class

* QueuedSocket.send()
* QueuedSocket.recv()
* QueuedSocket.close()
  These methods present the same API as the `agutil.io.Socket` class
