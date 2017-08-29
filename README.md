# agutil
* Master build status: [![Master Build Status](https://travis-ci.org/agraubert/agutil.svg?branch=master)](https://travis-ci.org/agraubert/agutil) [![Live Package Version](https://img.shields.io/pypi/v/agutil.svg)](https://pypi.python.org/pypi/agutil)
* Development build status: [![Dev Build Status](https://travis-ci.org/agraubert/agutil.svg?branch=dev)](https://travis-ci.org/agraubert/agutil) [![Dev Coverage Status](https://coveralls.io/repos/github/agraubert/agutil/badge.svg?branch=dev)](https://coveralls.io/github/agraubert/agutil?branch=dev)

A collection of python utilities

__Version:__ 2.0.0

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

* Dispatcher (A class for managing background threads for running tasks in parallel)
* parallelize (A decorator to easily convert a regular function into a parallelized version)

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

## Features in development:

## agutil.parallel (new module)
Added a new `agutil.parallel` module which includes the following:
* `agutil.parallel.Dispatcher`, a class which produces generators to yield values
returned by background threads executing tasks in parallel.
* `agutil.parallel.parallelize`, a decorator function to wrap a function with an
`agutil.parallel.Dispatcher` and yield from the Dispatcher's results

**Note:** Due to
[inherent issues with cpython](https://wiki.python.org/moin/GlobalInterpreterLock),
this system is not suited for CPU bound tasks. I/O bound tasks will, however, be able
to benefit from thread-based parallelization

##### API
* agutil.parallel.parallelize(_func_):

  Decorates _func_ and returns a function with an identical signature, except that
  in place of each argument or keyword argument, you should provide an iterable of
  arguments instead. The iterables will define the different calls made to _func_.
  The decorated function will return a **generator** which yields values **in order**
  (see the dispatcher return guarantee, below) from the background calls. The generator
  will call _func_ until the one of the argument iterables is exhausted. You may
  optionally call parallelize with a _maximum_ argument (ie: `@parallelize(10)` vs `@parallelize`)
  to change the maximum number of allowed threads.

## agutil.parallel.Dispatcher
This class takes a function and iterables of arguments to dispatch calls to the function
on background threads. The Dispatcher will execute calls the function using arguments
extracted from the iterables provided until one or more of the iterables is empty.
Multiple threads may concurrently iterate over the Dispatcher, or iterate over it
after it finishes running, but the Dispatcher cannot be restarted.  Re-iterating
over the Dispatcher will yield the same results

### Example:
* If you have a function _foo(n)_ which takes a single argument _n_ and you need
it to be called on 1, 2, and 3, you could make a dispatcher with:
`Dispatcher(foo, [1,2,3])` which would prepare three threads to call _foo(1)_,
_foo(2)_, and _foo(3)_, respectively.

##### API
* Dispatcher(_func_, _\*args_, _maximum=15_, _\*\*kwargs_): _(constructor)_

  Constructs a new Dispatcher.  _func_ is the function to run in the background.
  _maximum_ is the maximum number of background threads that are allowed to run at
  the same time (the `Dispatcher` will take care of starting and stopping threads
    as needed). The remaining _args_ and _kwargs_ provided should match the call
  signature of _func_, except that instead of providing single arguments, you should
  provide **iterables** of arguments.  The iterables will be used to dispatch threads
  in the background, in the order that arguments appear in the iterables.

* Dispatcher.run():

  Begins execution of the `Dispatcher` and returns a **generator**. Once this method
  is called for the first time, the `Dispatcher` will begin pulling arguments out
  of the iterables and start background threads up to the maximum allowed number.
  On subsequent calls to `run()`, the `Dispatcher` will immediately yield the same
  results out of its cache. If an exception is raised in one of the background threads,
  the thread will return the exception (the `Dispatcher` will yield this exception
  as this thread's return value) and halt , but the `Dispatcher` will continue to
  iterate and create new threads. If an exception is raised in `run()` during iteration,
  it will stop the `Dispatcher`; no more threads will be started, but threads which
  were already started will continue until they exit normally.
  `Dispatcher` makes the following guarantee about
  threads and return values:

  **Dispatcher return guarantee:** `Dispatcher` guarantees that threads will be started
  in the same order that arguments appear, and that data is returned by the generator
  in that same order. This has two consequences:
  * Threads may not finish in any particular order

    Due to the nature of threads, `Dispatcher` makes no guarantee regarding when
    any particular call to the function will finish.

  * Data may not be returned as soon as it is available

    To maintain the guarantee that data is returned in the correct order, the generator
    will block and wait for the right call to finish before yielding a value.

* Dispatcher.\_\_iter\_\_(): _(iteration)_

  Yields results from `Dispatcher.run()`.  This allows you to construct and immediately
  iterate over a `Dispatcher`.

* Dispatcher.isAlive():

  Returns True if the `Dispatcher` is still running
