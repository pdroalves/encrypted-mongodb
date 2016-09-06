"""A simple permutation for arbitrary length integers.

This file also includes a simple XORShift-based PRNG for expanding the seed.
Example code from http://www.jstatsoft.org/v08/i14/paper (public domain).
"""
import random

from .parameters import TRIPLETS


class Permutation(object):
    """Simple permutation object."""

    def __init__(self, bit_length=64, seed=None):
        """Set up the permutation object. `seed` can be any rundom number."""
        if seed is None:
            seed = random.randint(0, (1 << bit_length)-1)
        self.bit_length = bit_length
        self._mask = (1 << bit_length)-1
        xorshift = _XORShift(seed, self._mask)
        self._masks = tuple(xorshift() & ((1 << (i >> 1)) ^ self._mask)
                            for i in range(bit_length*2))

    def map_to(self, num):
        """Map a number to another random one."""
        return self._map(num, range(self.bit_length))

    def map_from(self, num):
        """The reverse of `map_to`. IOW `perm.map_from(perm.map(x)) == x`."""
        return self._map(num, range(self.bit_length-1, -1, -1))

    def _map(self, num, rng):
        """Logic used by both `map_to` and `map_from`."""
        for i in rng:
            bit = 1 << i
            if (bit & num) >> i == 0:
                num ^= self._mask ^ (self._masks[(i << 1)+((bit & num) >> i)] |
                                    (bit ^ bit & num))
            else:
                num ^= self._mask ^ (self._masks[(i << 1)+((bit & num) >> i)] |
                                    (bit & num))
        return num


class _XORShift(object):
    """XOR Shift implementation."""

    def __init__(self, seed, bitmask):
        self._seed = seed
        triplet = TRIPLETS[seed % len(TRIPLETS)]
        self._p_a, self._p_b, self._p_c = triplet
        self._bitmask = bitmask

    def __call__(self):
        self._seed ^= self._bitmask & (self._seed << self._p_a)
        self._seed ^= self._bitmask & (self._seed >> self._p_b)
        self._seed ^= self._bitmask & (self._seed << self._p_c)
        return self._seed
