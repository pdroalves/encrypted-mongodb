#!/usr/bin/python
import os
import sys
import getopt
import json
import generate_prime as Prime
import auxiliar as Aux
from cipher import Cipher
from Crypto.Random import random

class Paillier(Cipher):

	@staticmethod
	def keygen(key_size=1024):
		# Generates a new key set

		n = None
		p = None
		q = None
		while n is None or (p is not None and q is not None and Paillier.__egcd(n,(p-1)*(q-1))[0] != 1):
			while p is None or q is None:
				try:
					while p == q:
						p = Prime.generate_large_prime(key_size / 2)
						q = Prime.generate_large_prime(key_size / 2) # i want p != q
				except Exception,err:
					print err
					p = None
					q = None

			n = p*q
		
		g = n+1
		l = (p-1)*(q-1)# == phi(n)
		
		keys = {"pub":{
					"n":n,
					"g":g},
				"priv":{
				 "lambda":l
				 }
			   }

		return keys

	def set_deterministic(self,r=None):
		if r is None:
			pub = Cipher.get_public_key(self)
			r = random.randrange(1,pub["n"])
		Cipher.add_to_public_key(self,"r",r)
		return r
		
	def encrypt(self,m):
		if type(m) == str:
			m = int(m)
			
		assert Aux.is_int(m)

		pub = Cipher.get_public_key(self)
		assert pub.has_key("n")
		assert pub.has_key("g")

		n = pub["n"]
		n2 = n*n if not pub.has_key("n2") else pub["n2"]
		if not pub.has_key("n2"):
			pub["n2"] = n2
		g = pub["g"]
		r = pub["r"] if pub.has_key("r") else random.randrange(1,n)

		assert abs(m) < n		

		if m < 0:
			g_m__n2 = self.__modinv(pow(g,-m,n2),n2)
		else:
			g_m__n2 = pow(g,m,n2)

		c = g_m__n2*pow(r,n,n2) % n2
		return str(c)

	def decrypt(self,c):
		assert Aux.is_int(c)
		c = long(c)	

		pub = Cipher.get_public_key(self)
		priv = Cipher.get_private_key(self)

		assert pub.has_key('n')
		assert pub.has_key('g')
		assert priv.has_key('lambda')

		n = pub['n']
		n2 = n*n if not pub.has_key("n2") else pub["n2"]
		g = pub['g']
		l = priv['lambda']
		mi = pow(l,l-1,n)

		charmical_function = lambda u,n: (u-1)/n
		m = charmical_function(pow(c,l,n2),n)*mi % n
		return m

	def h_operation(self,a,b,mod=None,fix=None):
		assert Aux.is_int(a)
		assert Aux.is_int(b)
		a = long(a)	
		b = long(b)	

		if mod is None:
			mod = Cipher.get_public_key(self)["n2"]
		if fix is None:
			c = a*b % mod
		else:
			c = a*b*fix % mod

		return str(c)

	@staticmethod
	def __egcd(a, b):
	    x,y, u,v = 0,1, 1,0
	    while a != 0:
	        q, r = b//a, b%a
	        m, n = x-u*q, y-v*q
	        b,a, x,y, u,v = a,r, u,v, m,n
	    gcd = b
	    return gcd, x, y

	@staticmethod
	def __modinv(a, m):
	    gcd, x, y = Paillier.__egcd(a, m)
	    if gcd != 1:
	        return None  # modular inverse does not exist
	    else:
	        return x % m