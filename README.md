# agutil
* Master build status: [![Master Build Status](https://travis-ci.org/agraubert/agutil.svg?branch=master)](https://travis-ci.org/agraubert/agutil) [![Live Package Version](https://img.shields.io/pypi/v/agutil.svg)](https://pypi.python.org/pypi/agutil)
* Development build status: [![Dev Build Status](https://travis-ci.org/agraubert/agutil.svg?branch=dev)](https://travis-ci.org/agraubert/agutil) [![Dev Coverage Status](https://coveralls.io/repos/github/agraubert/agutil/badge.svg?branch=dev)](https://coveralls.io/github/agraubert/agutil?branch=dev)

A collection of python utilities

__Version:__ 3.0.0

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
* encryptFile and decryptFile (Simple methods for encrypting and decrypting local files)
* agutil-secure (A command line utility for encrypting and decrypting files)

## Documentation:
Detailed documentation of these packages can be found on the [agutil Github wiki page](https://github.com/agraubert/agutil/wiki)

## Installation note:
This package requires PyCrypto, which typically has issues compiling on windows.  If you are on windows and `pip install agutil` fails during the installation of PyCrypto, then follow the instructions [here](https://github.com/sfbahr/PyCrypto-Wheels) for installing PyCrypto from a precompiled wheel, and then run `pip install agutil` again.

## Features in Development:

### agutil.security

The following change has been made to the `agutil.security` module:
* The padding scheme has been changed to be more cryptographically secure:
  * Formerly, the padding scheme would append 1-16 bytes all with the same value
  (equaling the padding length)
  * Now, the padding scheme still appends the same number of bytes, but only the
  last byte of the string will have a value set to equal the padding length. The
  first n-1 bytes of padding are random bytes. A padded message will look like this:
  `Original Message` + `n-1 random bytes` + `literal [n] byte`
  * The new and old padding schemes are forwards and backwards compatible. The
  unpadding methods only examine the final byte of a message to determine the
  padding length, so old versions of `agutil` will still recognize new-padded strings
  (and visa-versa)

### agutil (main module)

The following change has been made to the `agutil` module:
* Added `first()` function to return the first element of an iterable matching a
given predicate

##### API

* first(iterable, predicate)

  Takes an _iterable_ and returns the first item for which _predicate_(item) is True.
  If _predicate_ is callable, it must be a function which takes a single argument
  (if the result of the function is 'Truthly' the item in the iterable will be returned).
  Alternatively, _predicate_ may be an object, in which case `first()` will return
  the first item in the _iterable_ which compares equal to the given _predicate_
  object

### agutil.status_bar

The following changes have been made to `agutil.status_bar`:
* The _value_ argument to `status_bar.update()` is now optional. If omitted, the
status bar will be incremented by one
* Added a `status_bar.iter()` class method. The goal of this function is to serve
as a wrapper for iterables to add a status bar to any loop

##### API

* status_bar.iter(cls, iterable, maximum=None, iter_debug=False,\*\*kwargs) _(class method, generator)_

  Takes an _iterable_ and yields elements from it while updating a status bar automatically.
  The _maximum_ argument is used to set the maximum of the created status bar.
  If _maximum_ is omitted or None, `len()` will be called on the iterable to determine
  its size. If _iter\_debug_ is True, this method will first yield the status bar
  before iterating over elements of the provided iterable (for debugging purposes).
  _kwargs_ are passed to the `status_bar` constructor.

* status_bar.update(value=None)

  updates the display iff _value_ would require a change in the length of the progress
  bar, or if it changes the percentage readout by at least _update\_threshold_.
  If _value_ is None, the bar's current value will be incremented by one.

### agutil.parallel
The following changes have been made to `agutil.parallel`:
* `parallelize` and `parallelize2` must now be called when used as decorators

  Example: `@parallelize()` or `@parallelize(12)`

* `parallelize` and `parallelize2` now take a _workertype_ argument to set if
parallelization will be thread or process based.
    * `agutil.parallel.WORKERTYPE_THREAD`: Use for thread-based parallelization
    (default)
    * `agutil.parallel.WORKERTYPE_PROCESS`: Use for process-based parallelization.
    **Note: Processed-based parallelization has several limitations**; see note
    below
* `agutil.parallel.Dispatcher` has been refactored and renamed to
`agutil.parallel.IterDispatcher`, but mostly follows the same syntax
* Added `agutil.parallel.DemandDispatcher` to be the dispatching backend for
`agutil.parallel.parallelize2` instead of relying on heavy logic within the function
* Added `agutil.parallel.ThreadWorker` to manage worker threads for thread-based
parallelization
* Added `agutil.parallel.ProcessWorker` to manage worker processes for process-based
parallelization

#### Multiprocessing note
Process-based parallelization has several limitations due to the implementation
of the builtin `pickle` module:
* You **CANNOT** use `paralellize` or `parallelize2` as decorators. You must call
them on a pre-defined function and assign the result to a function **with a different
name**.
* You **CANNOT** use `parallelize` or `parallelize2` on a function created within
another function's closure. You must call them on **globally accessible** functions

Example usage:
```python
def foo(arg):
  return arg + 1

bar = parallelize(workertype=WORKERTYPE_PROCESS)(foo)
```

Thread-based parallelization does not suffer these limitations and therefore
both `parallelize` and `parallelize2` can be used as decorators and on function-local
objects when using WORKERTYPE_THREAD (default)

##### API
* parallelize(_maximum_=15, _workertype_=WORKERTYPE_THREAD)

  Decorator **factory**. Returns a function which can be used to decorate another
  function. The decorated function has an identical signature, except that
  in place of each argument or keyword argument, you should provide an iterable of
  arguments instead. The iterables will define the different calls made to the
  _un_-decorated function. The decorated function will return a **generator**
  which yields values **in order** (see the dispatcher return guarantee, below)
  from the background calls. The generator will call the _un_-decorated function
  until one of the argument iterables is exhausted. The _maximum_ argument sets
  the maximum number of workers which can run at one time. You may set _workertype_ to
  `agutil.parallel.WORKERTYPE_PROCESS` to use process-based parallelization.
  Process-based parallelization is useful if your function is CPU-intensive but
  there are limitations which effect the syntax of `parallelize` (see note above)

* parallelize2(_maximum_=15, _workertype_=WORKERTYPE_THREAD)

  Decorator **factory**. Returns a function which can be used to decorate another
  function. The decorated function has an identical signature, but calls will return
  callback objects instead of function results. When called, the callback waits
  for the result from the associated call to return, then returns that
  value (or raises an exception if the call failed). The _maximum_ argument sets
  the maximum number of workers which can run at one time. You may set _workertype_ to
  `agutil.parallel.WORKERTYPE_PROCESS` to use process-based parallelization.
  Process-based parallelization is useful if your function is CPU-intensive but
  there are limitations which effect the syntax of `parallelize` (see note above).
  **Note:** `parallelize2` may encounter a substantially larger system overhead
  than `parallelize` or `dispatcher` when calling the decorated function many (>100) times

### Example: parallelize vs parallelize2
These two decorators provide essentially the same system of parallelization, with
slightly different flavors.  Given two functions `foo` and `bar`:
```python
@parallelize()
def foo(n):
  #Do some work
  return results

@parallelize2()
def bar(n):
  #Do the same work
  return results
```

Both `foo` and `bar` will perform the same tasks in roughly the same amount of time,
the only difference being how the functions are invoked.

```python
#get a list of results from foo, using parallelize
results_1 = [x for x in foo(range(100))]

#Start all the workers for bar, using parallelize2
tmp = [bar(x) for x in range(100)]
#Now wait for and retrieve the results
results_2 = [callback() for callback in tmp]
```

### When to use parallelize vs parallelize2

Both functions have advantages and disadvantages.

@parallelize is useful in the following conditions:
* You know exactly how many times you will call the function and you know what the arguments will be for each call
* You are going to iterate over the results

@parallelize2 is useful in the following conditions:
* You cannot determine in advance how many times the function will be called
* You may not need to iterate over the results, but simply need the results at some later point in time
* The function is not recursive


### parallelize2 recursion issues:
`agutil.parallel.parallelize2` enforces a maximum worker count (per-function) by putting workers to sleep until one of the running workers finishes. If a recursive function calls itself, it will immediately return the callback (standard behavior of parallelize2). However, if the maximum worker count has been reached, the worker for the recursive call will be put to sleep immediately. If the calling function then uses the callback to wait for the value, it may block forever unless another worker finishes:
```python
@agutil.parallel.parallelize2()
def func(args):
    # While this function is working, other calls to func()
    # fill up the remaining worker slots so future calls to func()
    # will be put to sleep until workers start finishing
    callback = func(args) # recursively call func()
    # This call to func is immediately put to sleep since the maximum
    # worker count has been reached.
    callback() # wait for the result
    # Unless one of the other workers finishes, the above function will block
    # forever

# For this specific example, calling func() will block forever on one call
# as the recursive calls take up worker slots until they start being put to sleep

func()() # blocks forever
```

`agutil.parallel.parallelize` can be used in recursive functions because the worker count is specific to each invocation, so a recursive call uses its own worker pool

### agutil.parallel.IterDispatcher
Added a new class, `agutil.parallel.IterDispatcher` which is derived from the old
`agutil.parallel.Dispatcher`. It takes a function and iterables of arguments and
then dispatches background calls and iterates over results as they become available

##### API
* IterDispatcher(_func_, \*_args_, _maximum_=15, _workertype_=WORKERTYPE_THREAD, \*\*_kwargs_): _(constructor)_

  Constructs a new `IterDispatcher` (similar to the old `Dispatcher` object).
  _func_ is the function to be run in the background. _maximum_ is the maximum
  number of background workers that will be allowed to run at once. _workertype_
  sets the type of workers that will be used (threads or processes) and can be either
  `agutil.parallel.WORKERTYPE_THREAD` or `agutil.parallel.WORKERTYPE_PROCESS`.
  The remaining _args_ and _kwargs_ should match the call signature of _func_,
  except that instead of providing single arguments, you should provide **iterables**
  of arguments (and keyword arguments). The iterables will be used to dispatch workers
  in the background, in the order that arguments appear in the iterables.

* IterDispatcher.run()

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

* IterDispatcher.\_\_iter\_\_(): _(iteration)_

  Yields results from `IterDispatcher.run()`. This allows you to construct and
  immediately iterate over an `IterDispatcher`

* IterDispatcher.is_alive():

  Returns True if the `IterDispatcher` is still running

### agutil.parallel.DemandDispatcher
Added a new class, `agutil.parallel.DemandDispatcher`, which implements the dispatching
logic of `agutil.parallel.parallelize2` which was previously contained in the function
itself

##### API
* DemandDispatcher(_func_, _maximum_=15, _workertype_=WORKERTYPE_THREAD): _(constructor)_

  Constructs a new `DemandDispatcher`. _func_ is the function to be executed and
  _maximum_ is the maximum number of background workers which can be executed at
  one time. _workertype_ sets the type of workers that will be used (threads or
  processes) and can be either `agutil.parallel.WORKERTYPE_THREAD` or
  `agutil.parallel.WORKERTYPE_PROCESS`.

* DemandDispatcher.dispatch(self, \*_args_, \*\*_kwargs_):

  Dispatches a new call to the function provided in the constructor. Immediately
  returns a callback object. Call the callback object to wait for and return the
  result of calling `func(*args, **kwargs)`. If an exception is raised during the
  background execution of the function, it will be raised here. Unlike `IterDispatcher`
  an exception encountered during background execution **will not** halt the execution
  of the `DemandDispatcher`. It is the programmer's responsibility to call
  `DemandDispatcher.close()` when finished. Exceptions encountered by the dispatcher
  itself will, however, halt the `DemandDispatcher` (no need to call `close()`).

* DemandDispatcher.close():

  Halts background workers and waits for cleanup tasks to complete

### agutil.parallel.ThreadWorker
Added a new class, `agutil.parallel.ThreadWorker`, which implements the thread management
previously used in `agutil.parallel.Dispatcher` with the goal of allowing more
modularity at the dispatcher level. `ThreadWorker` is best suited for IO-bound
tasks (reading files, executing shell commands, etc). For CPU-bound tasks, use a
`ProcessWorker`

##### API

* ThreadWorker(_maximum_): _(constructor)_

  Constructs a new `ThreadWorker`. _maximum_ sets the maximum number of threads
  which can be executed at once

* ThreadWorker.dispatch(_func_, \*_args_, \*\*_kwargs_):

  Queues a call to `func(*args, **kwargs)` with the `ThreadWorker`. This function
  immediately returns a callback object. Calling the callback object waits for and
  returns the result of `func(*args, **kwargs)`, or raises the exception encountered
  during the execution of that function. The `ThreadWorker` takes care of starting
  and stopping threads, and will dispatch the call once the number of active workers
  is below the maximum set in the constructor

* ThreadWorker.close():

  Shuts down the `ThreadWorker`. No more calls can be dispatched after calling
  this method. It is the programmer's responsibility to call this function when
  finished with the `ThreadWorker`

* ThreadWorker.is_alive():

  Returns True if this `ThreadWorker` has not been closed

### agutil.parallel.ProcessWorker
Added a new class, `agutil.parallel.ProcessWorker`, which implements a process
management backend for Dispatchers using `multiprocessing.Pool`. `ProcessWorker`
is best suited for CPU-bound tasks (mathematics, string manipulation, etc). `ThreadWorker`
is recommended for IO-bound tasks as `ProcessWorker` will carry a heavier overhead
per-worker.

##### API

* ProcessWorker(_maximum_): _(constructor)_

  Constructs a new `ProcessWorker` and creates a process pool using the assigned
  _maximum_ number of processes. **Be mindful of your hardware**; creating a
  `ProcessWorker` with more processes than there are available processor cores in
  your computer will cause performance drawbacks in both python and your system
  as a whole

* ProcessWorker.dispatch(_func_, \*_args_, \*\*_kwargs_):

  Queues a call to `func(*args, **kwargs)` with the `ProcessWorker`. This function
  immediately returns a callback object. Calling the callback object waits for and
  returns the result of `func(*args, **kwargs)`, or raises the exception encountered
  during the execution of that function. The `ProcessWorker` takes care of submitting
  the call to the underlying pool, which will be executed when one of the processes
  in the pool becomes available.

* ProcessWorker.close():

  Shuts down the `ProcessWorker`. No more calls can be dispatched after calling
  this method. It is the programmer's responsibility to call this function when
  finished with the `ProcessWorker`

* ProcessWorker.is_alive():

  Returns True if this `ProcessWorker` has not been closed
