# FastORE

This is a prototype implementation of the order-revealing encryption (ORE) schemes
described in the following papers:
  * [Practical Order-Revealing Encryption with Limited Leakage](https://eprint.iacr.org/2015/1125.pdf) (ore.h)
  * [Order-Revealing Encryption: New Constructions, Applications, and Lower Bounds](https://eprint.iacr.org/2016/612.pdf) (ore_blk.h)

This implementation is a research prototype and serves primarily as a proof of concept
and benchmarking tool for our cryptographic primitives. The code has not been carefully
analyzed for potential security flaws, and is not intended for use in production-level
code.

Authors:
 * David J. Wu, Stanford University
 * Kevin Lewi, Stanford University

Contact David for questions about the code:
  dwu4@cs.stanford.edu
  
Project Website: https://crypto.stanford.edu/ore/

## Prerequisites ##

Make sure you have the following installed:
 * [GMP 5](http://gmplib.org/)
 * [OpenSSL](http://www.openssl.org/source/)

Currently, our system requires a processor that supports the AES-NI instruction set.

## Installation ##

    git clone --recursive https://github.com/kevinlewi/fastore.git
    cd fastore
    make

## Running Tests ##

To test the basic ORE scheme (described in the first [paper](https://eprint.iacr.org/2015/1125.pdf)),
use the following command:

    ./tests/test_ore

To test the "block ORE" scheme (described in the second [paper](https://eprint.iacr.org/2016/612.pdf)),
use the following command:

    ./tests/test_ore_blk

## Running Benchmarks ##

To run the benchmarks, use the commands:

    ./tests/time_ore
    ./tests/time_ore_blk

## Additional Configuration ##

See `flags.h` for additional configuration changes that are possible.
