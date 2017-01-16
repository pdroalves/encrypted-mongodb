##########################################################################
##########################################################################
#
# mongodb-secure
# Copyright (C) 2016, Pedro Alves and Diego Aranha
# {pedro.alves, dfaranha}@ic.unicamp.br

# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.

# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.

# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
##########################################################################
##########################################################################
import random
import math
import sys

def miller_rabin(p,s=11):
    # using security parameter s=11, we have a error probability of less than
    # 2**-80

    #computes p-1 decomposition in 2**u*r
    r = p-1
    u = 0
    while r&1 == 0:#true while the last bit of r is zero
        u += 1
        r = r/2

    # apply miller_rabin primality test
    for i in range(s):
        a = random.randrange(2,p-1) # choose random a in {2,3,...,p-2}
        z = pow(a,r,p)

        if z != 1 and z != p-1:
            for j in range(u-1):
                if z != p-1:
                    z = pow(z,2,p)
                    if z == 1:
                        return False
                else:
                    break
            if z != p-1:
                return False
    return True


def is_prime(n):
     #lowPrimes is all primes (sans 2, which is covered by the bitwise and operator)
     #under 1000. taking n modulo each lowPrime allows us to remove a huge chunk
     #of composite numbers from our potential pool without resorting to Rabin-Miller
     lowPrimes =   [2,3,5,7,11,13,17,19,23,29,31,37,41,43,47,53,59,61,67,71,73,79,83,89,97
                   ,101,103,107,109,113,127,131,137,139,149,151,157,163,167,173,179
                   ,181,191,193,197,199,211,223,227,229,233,239,241,251,257,263,269
                   ,271,277,281,283,293,307,311,313,317,331,337,347,349,353,359,367
                   ,373,379,383,389,397,401,409,419,421,431,433,439,443,449,457,461
                   ,463,467,479,487,491,499,503,509,521,523,541,547,557,563,569,571
                   ,577,587,593,599,601,607,613,617,619,631,641,643,647,653,659,661
                   ,673,677,683,691,701,709,719,727,733,739,743,751,757,761,769,773
                   ,787,797,809,811,821,823,827,829,839,853,857,859,863,877,881,883
                   ,887,907,911,919,929,937,941,947,953,967,971,977,983,991,997]
     if (n >= 3):
         if (n&1 != 0):
             for p in lowPrimes:
                 if (n == p):
                    return True
                 if (n % p == 0):
                     return False
             return miller_rabin(n)
     elif n == 2:
         return True
     return False

def generate_large_prime(k):
    #print "Generating prime of %d bits" % k
    #k is the desired bit length
    r=100*(math.log(k,2)+1) #number of attempts max
    while r>0:
        #randrange is mersenne twister and is completely deterministic
        #unusable for serious crypto purposes
        n = random.randrange(2**(k-1),2**(k))
        r-=1
        if is_prime(n) == True:
            return n
    raise Exception("Failure after %d tries." % r)
