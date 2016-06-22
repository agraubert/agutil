# agutil
[![Build Status](https://travis-ci.org/agraubert/agutil.svg?branch=master)](https://travis-ci.org/agraubert/agutil)

A collection of python utilities

###### Tools:
* search_range (A utility for manipulating numerical ranges)
* status_bar (A simple progress bar indicator)


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
    * status_bar(maximum, show_percent = False, init=True,  cols=int(get_terminal_size()[0]/2), update_threshold=.00005, debugging=False) _(constructor)_
      Creates a new status_bar instance ranging from 0 to _maximum_
      _show_percent_ toggles whether or not a percentage meter should be displayed to the right of the bar
      _init_ sets whether or not the status_bar should immediately display.  If set to false, the bar is displayed at the first update
      _cols_ sets how long the bar should be.  It defaults to half the terminal size
      _update_threshold_ sets the minimum change in percentage to trigger an update to the percentage meter
      _debugging_ triggers the status_bar to never print to stdout.  If set true, no output will be produced, but exact string of what *would* be displayed is maintained at all times in the _display_ attribute

    * status_bar.update(value)
      updates the display iff _value_ would require a change in the length of the progress bar, or if it changes the percentage readout by at least _update_threshold_

    * status_bar.clear(erase=False)
      Clears the readout from stdout
      If _erase_ is true, the readout is cleared entirely
      Otherwise, the cursor position is simply reset to the front of the bar, which will overwrite characters in the readout with subsequent output to stdout by any source
