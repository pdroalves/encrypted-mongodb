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

class ORESMALL():
    F = None
    pi = None
    sk = None

    # Generates a key using a hash of some passphrase
    def keygen( self, passphrase,n = 16 ):
        self.n = n
    	k = PRF.keygen(passphrase)
        pi = URP(n=self.n,seed=42)

        self.F = PRF()
        self.F.add_to_private_key("key",k)

        for i in xrange(n):
            self.F.encrypt(i)#Pre-computation

        self.sk = (k,pi)
    	return self.sk

    def encryptL( self, sk, x ):
        assert log(x,2) < self.n
    	assert type(x) in (int,long)
        k,pi = sk
        pi.refresh()

        h = pi.map_to(x)
    	ctL = (
	    		self.F.encrypt( h ),
	    		h
    		)
    	return ctL

    def encryptR( self, sk, y ):

    	assert type(y) in (int,long)
        assert log(y,2) < self.n

        k,pi = sk

        pi.refresh()

        r = numpy.random.bytes(128).encode("hex")

    	bits = bin(y).partition("b")[2]

    	v = [None]*self.n

        ctR = [r]
        for i in range(self.n):
            ctR.append( 
                        (
                            self.cmp( pi.map_from(int(i)), y ) + 
                                    H ( self.F.encrypt(int(i)) , r )
                        ) % 3
                    )
    	return ctR

    def encrypt( self, y, sk = None ):
        if sk is None:
            sk = self.sk
        k,pi = sk
        assert log(y,2) < self.n
        return (self.encryptL(sk, y), self.encryptR(sk, y))

    @staticmethod
    def compare( ctL, ctR ):
        global H

        kl,h = ctL
        r,v = ctR[0],ctR[1:]
        print "hash: " + str(H(kl,r))
        
        result =  (v[h] - H(kl , r)) % 3 
        return result

    def cmp( self,a,b ):
        assert type(a) in (int,long)
        assert type(b) in (int,long)

        if a < b:
            return -1
        elif a == b:
            return 0
        else:
            return 1

# ore = ORESMALL()
# sk = ore.keygen("oi")
# ctA = ore.encrypt(sk, 9)
# ctB = ore.encrypt(sk, 10)
# ctC = ore.encrypt(sk, 11)
# ctD = ore.encrypt(sk, 11)

# assert ORESMALL.compare(ctA[0], ctB[1]) == 2
# assert ORESMALL.compare(ctB[0], ctB[1]) == 0
# assert ORESMALL.compare(ctC[0], ctB[1]) == 1
# assert ORESMALL.compare(ctB[0], ctA[1]) == 1
# assert ORESMALL.compare(ctC[0], ctA[1]) == 1
# assert ORESMALL.compare(ctD[0], ctB[1]) == 1

# print "All tests passed!"