Integer Permutation
===================

.. image:: https://d2weczhvl823v0.cloudfront.net/attilaolah/intperm.py/trend.png
   :target: https://bitdeli.com/free
   :alt: Bitdeli
.. image:: https://travis-ci.org/attilaolah/intperm.py.png?branch=master
   :target: https://travis-ci.org/attilaolah/intperm.py
   :alt: Build Status
.. image:: https://coveralls.io/repos/attilaolah/intperm.py/badge.png?branch=master
   :target: https://coveralls.io/r/attilaolah/intperm.py
   :alt: Coverage Status

This package implements a simple, configurable permutation on the set of 64-bit
integers.

The permutation is based on a bitmask that maps each bit of the input to a bit
of the output. The bitmask is expanded from a random seed using a PRNG_, as
described by *George Marsaglia* in his paper called `Xorshift RNGs`_. The
permutations are thus believed to be unpredictable, provided provided that the
seed is kept secret.

.. _PRNG: https://en.wikipedia.org/wiki/Pseudorandom_number_generator
.. _Xorshift RNGs: http://www.jstatsoft.org/v08/i14/paper

Usage
-----

Create a new ``Permutation`` instance by passing in an optional seed.

.. code:: python

    >>> fromo intperm import Permutation
    >>> perm = Permutation(42)
    >>> perm.map_to(37)
    13750393542137160527L
    >>> perm.map_from(13750393542137160527)
    37

Not providing a seed will create a random permutation:

.. code:: python

    >>> perm = Permutation()
    >>> perm.map_from(perm.map_to(37)) == 37
    True

Use cases
---------

Use cases may vary, but an example that I find useful is generating
hard_-to-guess, random-looking tokens based on IDs stored in a database.
The IDs can be used together with the seed to decode the original ID, but their
cardinality_ is the same as that of the IDs themselves. When used smartly,
this can save you from having to index those tokens in the database.

Another good example is randomising IDs of private objects that are available
via some sort of an API. Let's say the user accounts on your website are
accessible via the path ``/user/:id``, where ``:id`` is the user's ID. Someone
could track the growth of your user base just by enumerating the URLs and
keeping track of the status codes (e.g. 403 vs. 404).

Using this simple permutation, user IDs can be kept unpredictable, rendering
these kinds of attacks practically useless.

.. _hard: https://en.wikipedia.org/wiki/NP-hard
.. _cardinality: https://en.wikipedia.org/wiki/Cardinality

See also
--------

This library is also implemented in Ruby_ and Go_.

.. _Ruby: https://github.com/attilaolah/intperm.rb
.. _Go: https://github.com/attilaolah/intperm.go
