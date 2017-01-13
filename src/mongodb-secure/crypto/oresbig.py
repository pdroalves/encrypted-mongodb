#!/usr/bin/env python
#coding:utf-8
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
import base64
import hashlib
import hashlib
import numpy
import intperm as PRP
from operator import xor
from aesdet import AESDet as PRF
from urpint import URPINT as URP
from math import log

# F  => PRF: AES-128
# pi => PRP: IntPerm 
# H  =>HASH: SHA256

H = lambda x,y: int(hashlib.sha256(x+y).hexdigest(),16) % 3
to_int = lambda x: int(hashlib.sha256(x).hexdigest(),16)
class OREBIG():
    d = None
    n = None


    # Generates a key using a hash of some passphrase
    # message space size N > 0
    # d-ary strings x = x_1x_2x_3...x_n
    def keygen( self, passphrase,d = 100, n = 3 , N = 512):
        self.n = n
        k1 = PRF.keygen(passphrase+"1")
    	k2 = PRF.keygen(passphrase+"2")
        pi = URP(n=d,seed=42) # pi(a,b) = PRP(a)*b

        sk = (k1,k2,pi)
        self.d = d
        self.n = n
        assert pow(d,n) >= N
    	return sk

    def encryptL( self, sk, x ):
        assert type(x) in (str,unicode)
        assert len(x) == self.n

        k1,k2,pi = sk
        pi.refresh()
        F1 = PRF()
        F1.add_to_private_key("key",k1)
        F2 = PRF()
        F2.add_to_private_key("key",k2)

        u = [None]*self.n

        for i in range(self.n):
            seqs = x[:i-1] if i >= 0 else ""
            z = pi.map_to( to_int(F2.encrypt(seqs)) % self.d )
            u[i] = F1.encrypt(seqs + str(z)), z
    	return u

    def encryptR( self, sk, y ):
        assert type(y) in (str,unicode)
        assert len(y) == self.n

        k1,k2,pi = sk
        pi.refresh()

        r = numpy.random.bytes(128)
        F1 = PRF()
        F1.add_to_private_key("key",k1)
        F2 = PRF()
        F2.add_to_private_key("key",k2)

    	v = [None]*self.n
        for i in range(self.n):
            u = [None]*self.d
            for j in range(self.d):
                seqs = y[:i-1] if i >= 0 else ""
                jl = pi.map_from( to_int(F2.encrypt(seqs))% self.d  )
                zij = (self.cmp(jl, ord(y[i])) + H( F1.encrypt(seqs + str(j)), r )) % 3

                u[j] = zij
            v[i] = u 
    	return [r] + v

    def encrypt( self, sk, y ):
        return (self.encryptL(sk, y), self.encryptR(sk, y))

    @staticmethod
    def compare( ctL, ctR ):
        global H

        u = ctL
        r,v = ctR[0],ctR[1:]

        n = len(u)

        for i in range(n):
            kli,hi = u[i]
            vi = v[i]

            result = (vi[hi] - H(kli,r)) % 3
            if result != 0:
                return result
        return 0

    def cmp( self,a,b ):
        assert type(a) in (int,long)
        assert type(b) in (int,long)

        if a < b:
            return -1
        elif a == b:
            return 0
        else:
            return 1

ore = OREBIG()
sk = ore.keygen("oi")
ctA = ore.encrypt(sk, "ABC")
ctB = ore.encrypt(sk, "BAC")
ctC = ore.encrypt(sk, "BCA")

assert OREBIG.compare(ctA[0], ctB[1]) == 1
assert OREBIG.compare(ctB[0], ctB[1]) == 0
assert OREBIG.compare(ctC[0], ctB[1]) == 2

print "All tests passed!"