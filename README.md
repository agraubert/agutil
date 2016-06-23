# agutil
* Master build status: [![Build Status](https://travis-ci.org/agraubert/agutil.svg?branch=master)](https://travis-ci.org/agraubert/agutil)
* Development build status: [![Build Status](https://travis-ci.org/agraubert/agutil.svg?branch=dev)](https://travis-ci.org/agraubert/agutil)

A collection of python utilities

###### Tools:
* search_range (A utility for manipulating numerical ranges)
* status_bar (A simple progress bar indicator)


The __bio__ package:
* maf2bed (A command line utility for parsing a .maf file, converting coordinates from 1-based (maf standard) to 0-based (bed standard))
* tsvmanip (A command line utility for filtering, rearranging, and modifying tsv files)


## SEARCH_RANGE
The `agutil.search_range` module defines a single class, `search_range`
A `search_range` class instance keeps track of a set of numerical ranges
Any number of ranges can be included or excluded from the instance
A single point, or range of points can be checked against the instance for intersection
Multiple instances can be combined with union, difference, and intersection operators to produce new `search_ranges`
The set of points in the search range is implemented as a bitset for efficiency

###### API
* search_range(start=0, stop=0, fill=True) _(constructor)_
  Creates a new `search_range` instance with the range [_start_, _stop_) included
  `search_range.check(i)` will return True for any point within [_start_, _stop_)

* search_range.add_range(start, stop)
  Adds the range [_start_, _stop_) to the set of points in the search range

* search_range.remove_range(start, stop)
  Removes the range [s_tart_, _stop_) from the set of points in the search range

* search_range.check(coord)
  Returns True if _coord_ exists within the set of points included in the search range
  Returns False otherwise

* search_range.check_range(start, stop)
  Returns True if any point within the range [_start_, _stop_) is included in the search range
  Returns False otherwise

* search_range.union(other)
* search_range.difference(other)
* search_range.intersection(other)
  Returns a new search_range whose set of points is the result of the union, difference, or intersection (respectively) of this search_range and _other_
  These methods can also be accessed through the following binary operators:
    * Union: _a|b_   _a+b_
    * Difference: _a-b_
    * Intersection: _a&b_   _a*b_

* search_range.__iter__() _(iteration)_
  search_ranges support iteration, which produces a sequence of points included in the range

* search_range.gen_ranges()
  Returns a generator which yields pairs of [start, stop) coordinates for each continuous set of points in the range

* search_range.range_count()
  Returns the number of points included in the range

* search_range.__str__()
  Produces a string which lists the ranges produced by gen_ranges()

* search_range.__repr__()
  Produces a string which lists each point included in the range

* search_range.__bool__()
  Returns True if there is at least one point included in the range

## STATUS_BAR
The `agutil.status_bar` module defines a single class, `status_bar`
A `status_bar` instance provides a status indicator which can be updated at any time
The display is only updated when necessary, so there is minimal drawback for updating the instance frequently

###### API
* status_bar(maximum, show_percent = False, init=True, prepend="", append="", cols=int(get_terminal_size()[0]/2), update_threshold=.00005, debugging=False, transcript=None) _(constructor)_
  Creates a new status_bar instance ranging from 0 to _maximum_

  _show_percent_ toggles whether or not a percentage meter should be displayed to the right of the bar

  _init_ sets whether or not the status_bar should immediately display.  If set to false, the bar is displayed at the first update

  _prepend_ is text to be prepended to the left of the bar.  It will always remain to the left of the bar as the display updates.  **WARNING** Prepended text offsets the bar.  If any part of the bar (including prepended or appended text) extends beyond a single line on the console, the status bar will not display properly.  Prepended text should be kept short

  _append_ is text to be appended to the right of the bar.  It will always remain to the right of the bar as the display updates.  **WARNING** Appended text extends the display.  If any part of the bar (including prepended or appended text) extends beyond a single line of the console, the status bar will not display properly.  Appended text should be kept short

  _cols_ sets how long the bar should be.  It defaults to half the terminal size

  _update_threshold_ sets the minimum change in percentage to trigger an update to the percentage meter

  _debugging_ triggers the status_bar to never print to stdout.  If set true, no output will be produced, but exact string of what *would* be displayed is maintained at all times in the _display_ attribute

  _transcript_ is a filepath to where the status bar should keep a log of all changes to the display.  If _transcript_ is None (the default value) or False, logging is disabled.  **WARNING** Using the transcript will slow down performance by requiring the status bar to make frequent i/o every time the display is modified.  Useful for debugging issues with prepended or appended text, but not recommended if the transcript is not needed

* status_bar.update(value)
  updates the display iff _value_ would require a change in the length of the progress bar, or if it changes the percentage readout by at least _update_threshold_

* status_bar.clear(erase=False)
  Clears the readout from stdout
  If _erase_ is true, the readout is cleared entirely
  Otherwise, the cursor position is simply reset to the front of the bar, which will overwrite characters in the readout with subsequent output to stdout by any source

* status_bar.prepend(text)
  Displays _text_ to the left of the bar. It will always remain to the left of the bar as the display updates.  **WARNING** Prepended text offsets the bar.  If any part of the bar (including prepended or appended text) extends beyond a single line on the console, the status bar will not display properly.  Prepended text should be kept short

* status_bar.append(text)
  Displays _text_ to the right of the bar.  It will always remain to the right of the bar as the display updates.  **WARNING** Appended text extends the display.  If any part of the bar (including prepended or appended text) extends beyond a single line of the console, the status bar will not display properly.  Appended text should be kept short

## bio.MAF2BED
The `agutil.bio.maf2bed` module provides a command line interface for converting maf files into bed files
To follow the bed format, and to reduce the size of the bed itself, maf2bed generates two files by default.
A `.bed` file with entries in the format of: Chromosome Start Stop Key
and a `.key` file with entries in the format of: Key <All fields present in the maf>

######COMMAND LINE API
* `$ maf2bed convert <input> <output> [--exclude-silent] [--skip-keyfile]`
  Converts the file _input_ to _output_ and _output_.key files.
  If _--exclude-silent_ is set, silent mutations are not included in the output
  If _--skip-keyfile_ is set, the program only generates a single file, _output_ which is identical to the _input_ file, except that start and stop coordinates have been shifted to 0-based

* `$ maf2bed lookup <input> <keys...>`
  Looks up the entries for each key listed in _keys_ in the keyfile _input_


## bio.TSVMANIP
The `agutil.tsvManip` module provides a command line interface for modifying large tsv files
While not _strictly_ biology oriented, its original purpose was to parse and rearrange different fields of bed files

######COMMAND USAGE
* `$ tsvmanip <input> <output> [--no-headers] [-c COLUMN] [-d DELIMITER] [--i0 COL] [-s COL] [-m IN:OUT] [-v]`

  Parses _input_ according to the following arguments, and writes to _output_

  Optional arguments:

  _--no-headers_          Flag indicating that there are is no header row

  _-c COLUMN, --col COLUMN_
                        Column containing input data to parse (0-indexed).
                        Multiple columns can be selected by providing the
                        option multiple times (Ex: --col 0 --col 5 --col 6).
                        All columns are selected by default

  _-d DELIMITER, --delim DELIMITER_
                        Delimiters for splitting input columns into multiple
                        new columns for output Delimiters can be specified for
                        multiple columns by providing the option multiple
                        times Delimiters are matched to colums by order
                        provided. For example, the first delimiter provided
                        matches to the first column parsed for input. An
                        underscore (\_) indicates no delimiter for that column.
                        To use a delimiter consisting entirely of one or more
                        underscores, append a single underscore to the end of
                        the delimiter string. (Ex: '--delim \__' (two
                        underscores) indicates a delimiter of '\_' (one
                        underscore) ). Multiple delimiters can be provided for
                        the same column by prefixing the delimiters for the
                        string with <column #>: Delimiters for the same column
                        are applied in the order provided to all resulting
                        columns from subsequent splits. Prefixed delimiter
                        inputs will not affect the matching of unprefixed
                        delimiters to columns. (Ex: --col 0 --col 1 --delim
                        <used for col 0> --delim <used for col 1>) (Ex: --col
                        1 --col 4 --delim <used for col 1> --delim <used for
                        col 4> --delim 1:<used for col 1>)

  _--i0 COL_              Selected columns should be shifted from 1 to 0 index.
                        This is applied after selected columns are plucked
                        from the input, and split by delimiters. Provided
                        column numbers match the indecies of columns after
                        those steps. Multiple columns can be selected by
                        supplying the argument multiple times

  _-s COL, --strip-commas COL_
                        Strip commas from the specified columns. Column
                        numbers reference before mapping, but after splitting

  _-m IN:OUT, --map IN:OUT_
                        Mappings to map plucked columns to output columns. Use
                        to change the order of columns. Maps are in the format
                        of: <input column #>:<output column #> This is the
                        last step in parsing, so input column #'s should be
                        relative to any changes made by plucking and splitting

  _-v_                    Provide verbose output
