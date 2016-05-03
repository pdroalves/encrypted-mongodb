#!/usr/bin/python
import numpy as np
from math import log,ceil
from cipher import Cipher
import BFIBE

class IBE(Cipher):

	def __init__(self,keys=None):
		self.keys = keys

	@staticmethod
	def keygen():
		# Computes a pair of master keys
		[[sign,msk],[x,y,z,norm]] = BFIBE.masterkeygen();

		# Format and return
		# msk = sign*__build_integers(words,64)
		mpk = {"x":x,"y":y,"z":z,"norm":norm}

		return {"msk":[long(x) for x in msk],"mpk":mpk}

	def private_keygen(self,identity):
		msk = self.keys["priv"]["msk"]
		assert type(msk) in [tuple,list]
		assert type(identity) is str
		assert all(isinstance(item, long) for item in msk)

		[x,y,z,norm] = BFIBE.keygen_prv(tuple([identity]+msk))
		return {"x":x,"y":y,"z":z,"norm":norm}

	def encrypt(self,identity,pt):
		assert type(self.keys["priv"]["mpk"]) is dict
		assert type(identity) is str
		assert type(pt) in (tuple,list)
		assert all(isinstance(item, int) for item in pt)

		nct = len(pt) + 2*32 + 1

		return [int(x) for x in 
					BFIBE.encrypt( 
								tuple( [identity,
										self.keys["priv"]["mpk"]["x"],
										self.keys["priv"]["mpk"]["y"],
										self.keys["priv"]["mpk"]["z"],
										self.keys["priv"]["mpk"]["norm"]]),
								np.array(pt,dtype=np.uint8),
								np.array([0]*nct,dtype=np.uint8)
							)
				]

	def decrypt(self,sk,ct):
		assert type(sk) is dict
		assert type(ct) in (tuple,list)
		assert all(isinstance(item, int) for item in ct)

		npt = len(ct) - 2*32 - 1

		return BFIBE.decrypt(
								tuple( [sk["x"],sk["y"],sk["z"],sk["norm"]]),
								np.array([0]*npt,dtype=np.uint8),
								np.array(ct,dtype=np.uint8)
						)

	def __get_words(self,a,word_size):
		mask = 2**word_size-1

		words = []
		while a > 0:
			word = a&mask
			words.append(word)

			a = a>>word_size

		return words

	def __build_integers(self,words,word_size):
		if len(words) == 0:
			return 0

		a = 0
		for i,word in enumerate(words):
			a = a + (word<<(word_size*i))
		return a