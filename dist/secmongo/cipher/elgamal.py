#!/usr/bin/python
#coding: utf-8
###########################################################################
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
import sys
import getopt
import random
import json
import os
import generate_prime as Prime
import auxiliar as Aux
from Crypto.Random import random
from cipher import Cipher

class ElGamal(Cipher):

    def __init__(self,keys=None,exponential_mode=False):
        self.exponential_mode = exponential_mode
        Cipher.__init__(self,keys)
    
    @staticmethod
    def keygen(key_size=1024):
        #
        # Public key: (p,alpha,beta)
        # Private key: (d) 
        #
        p = None
        while p is None:
            try:
                p = Prime.generate_large_prime(key_size)
            except Exception,err:
                print err


        alpha = random.randrange(1,p) # if |G| is prime, then all elements a not 1 \in G are primitives
        d = random.randrange(2,p-1)# from 2 to p-2
        beta = pow(alpha,d,p)

        keys = {"pub":{
                    "p":p,
                    "alpha":alpha,
                    "beta":beta},
                "priv":{
                 "d":d
                 }
               }
        return keys
    
    def set_deterministic(self,km=None):
        if km is None:
            pub = Cipher.get_public_key(self)
            i = random.randrange(2,pub["p"]-1)
            km = pow(pub["beta"],i,pub["p"])
        Cipher.add_to_public_key(self,"km",km)
        return km
        
    def encrypt(self,m):
        #
        # Encrypts a single integer
        #

        if type(m) == str:
            m = int(m)
            
        assert Aux.is_int(m)
        
        pub = Cipher.get_public_key(self)

        assert pub.has_key("p")
        assert pub.has_key("alpha")
        assert pub.has_key("beta")

        p = pub["p"]
        alpha = pub["alpha"]
        beta = pub["beta"]
        km = pub["km"] if pub.has_key("km") else None

        if self.exponential_mode:
            if m < 0:
                x = self.__modinv(pow(alpha,-m,p),p)
            else:
                x = pow(alpha,m,p)
        else:
            x = m

        if not km:
            i = random.randrange(2,p-1)
            ke = pow(alpha,i,p)
            km = pow(beta,i,p)

            c = (x*km) % p
            return c,ke
        else:
            c = (x*km) % p
            return c

    def decrypt(self,x):
        #
        # Decrypts a single integer
        #
        pub = Cipher.get_public_key(self)
        priv = Cipher.get_private_key(self)

        assert pub.has_key("p")
        assert priv.has_key("d")

        p = pub["p"]
        d = priv["d"]
        if type(x) == list and len(x) == 2:
            c = x[0]
            ke = x[1]
        else:
            c = x
        km = pub["km"] if pub.has_key("km") else pow(ke,d,p)

        inv = self.__modinv(km,p)

        return c*inv % p

    def generate_lookup_table(self,a=0,b=10**3):
        #
        # Receives an base g, prime p, a public key pub and a interval [a,b],
        # computes and encrypts all values g**i mod p for a <= i <= b and 
        # returns a lookup table
        #
        pub = Cipher.get_public_key(self)

        alpha = pub["alpha"]
        p = pub["p"]

        table = {}
        for i in xrange(a,b):
            c = pow(alpha,i,p)
            table[c] = i
        return table

    def h_operation(self,a,b):
        return a + b

    def __modinv(self,x,p):
        #
        # Computes the moduler inversion of x ** p-2 mod p,
        # for p prime
        #
        #return pow(x,p-2,p)
        return pow(x,p-2,p)