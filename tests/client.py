#!/usr/bin/python
# coding: utf-8

# 	This class is a conceptual implementation of the behavior that a standard user
# should adopt to interact with mongodb-secure 

import cipher.cipher as dummy_cipher
import cipher.aes as aes
import cipher.ibe as ibe
import cipher.paillier as paillier
import cipher.elgamal as elgamal
from pyope import ope
from datetime import timedelta
from datetime import date

class Client:
	__supported_attr_types = ["static","keyword","h_add","h_mul","range","do_nothing"]
	__keyword_attr = "keywords"
	__mapped_attr = {__keyword_attr:"keyword"}
	ciphers = {}
	
	def __init__(self,keys,ope_in_range=ope.ValueRange(0,10**6),ope_out_range=ope.ValueRange(0,10**8)):

        # Initializes all ciphers
		AES = aes.AES()
		AES.add_to_private_key("key",keys["AES"])

		Paillier = paillier.Paillier()
		Paillier.add_to_private_key("lambda",keys["Paillier"]["priv"]["lambda"])
		Paillier.add_to_public_key("n",keys["Paillier"]["pub"]["n"])
		Paillier.add_to_public_key("g",keys["Paillier"]["pub"]["g"])

		ElGamal = elgamal.ElGamal()
		ElGamal.add_to_public_key("p",keys["ElGamal"]["pub"]["p"])
		ElGamal.add_to_public_key("alpha",keys["ElGamal"]["pub"]["alpha"])
		ElGamal.add_to_public_key("beta",keys["ElGamal"]["pub"]["beta"])
		ElGamal.add_to_private_key("d",keys["ElGamal"]["priv"]["d"])

		IBE = ibe.IBE(keys["IBE"])
		IBE.add_to_private_key("msk",keys["IBE"]["msk"])
		IBE.add_to_private_key("mpk",keys["IBE"]["mpk"])

		OPE = ope.OPE(keys["OPE"],in_range=ope_in_range,out_range=ope_out_range)

		Dummy = dummy_cipher.Cipher()

		self.ciphers = {"static":AES,
						"keyword":IBE,
						"h_add":Paillier,
						"h_mul":ElGamal,
						"range":OPE,
						"do_nothing":Dummy}

	# Generates all keys
	@staticmethod
	def keygen():
		keys = {}
		keys["AES"] = aes.AES.keygen("password")
		keys["OPE"] = aes.AES.keygen("password")
		keys["Paillier"] = paillier.Paillier.keygen()
		keys["ElGamal"] = elgamal.ElGamal.keygen()
		keys["IBE"] = ibe.IBE.keygen()
		keys["IBE"].update({"identity":"Pedro"})

		return keys

	# Encrypts a query
	# 
	# pt: plaintex
	# kind: defines the purpose for which the document should be encrypted
	# parent: the parent key
	def encrypt(self,pt,kind = "store",parent = None):	
		assert type(pt) == dict

		ciphers = self.ciphers
		result = {}
		# finds the lef
		for key in pt:
			if type(pt[key]) == dict:
				result[key] = self.encrypt(pt[key],kind=kind,parent=key)
			elif parent in ["$inc","$dec","$set"]:
				# Update query
				op_kind = self.__mapped_attr[key]
				
				cipher = ciphers[op_kind]
				result[key] = cipher.encrypt(pt[key])

			elif key == "$in":
				if type(pt[key]) not in [list,tuple]:
					result[key] = list(pt[key])
				# Inside
				op_kind = self.__mapped_attr[parent]
				cipher = ciphers[op_kind]
				
				# Encrypts all items
				result[key] = []
				for value in pt[key]:
					ct = cipher.encrypt(value)
					result[key].append(ct)

			elif self.__mapped_attr[key] == "keyword":
				# Encrypts as keyword for storage
				if type(pt[key]) in [tuple,list]:	
					if self.__keyword_attr not in result.keys():
						result[self.__keyword_attr] = []

					op_kind = "keyword"
					cipher = ciphers[op_kind]

					for keyword in pt[key]:
						ct = cipher.encrypt(keyword,[1])
						result[self.__keyword_attr].append(ct)

				else:
					op_kind = "keyword"
					cipher = ciphers[op_kind]

					ct = cipher.encrypt(pt[key],[1])
					result[self.__keyword_attr] = ct

				# Encrypts as static		
				if 	kind == "store" and key != self.__keyword_attr and kind not in ["search","update"]:
					op_kind = "static"
					cipher = ciphers[op_kind]
					result[key] = cipher.encrypt(pt[key])
			else:
				if kind in ["search","update"]:
					continue
				op_kind = self.__mapped_attr[key]
				cipher = ciphers[op_kind]
				result[key] = cipher.encrypt(pt[key])
		return result

	# Decrypts the return of a query
	def decrypt(self,ct):	
		assert type(ct) == dict

		ciphers = self.ciphers

		result = {}
		# finds the lef
		for key in ct:
			if key == self.__keyword_attr:
				# There is no feasible to decrypt a keyword
				continue
			elif key == "_id":
				result[key] = ct[key]
			elif type(ct[key]) == dict:
				result[key] = self.decrypt(ct[key])
			elif type(ct[key]) in [tuple,list]:	
				op_kind = self.__mapped_attr[key]
				cipher = ciphers[op_kind]

				for value in ct[key]:
					pt = cipher.decrypt(value)
					result[self.__keyword_attr].append(pt)
			elif self.__mapped_attr[key] == "keyword":
				# Decrypt the static version
				op_kind = "static"
				cipher = ciphers[op_kind]

				pt = cipher.decrypt(ct[key])
				result[key] = pt
			else:
				op_kind = self.__mapped_attr[key]
				cipher = ciphers[op_kind]

				pt = cipher.decrypt(ct[key])
				result[key] = pt

		return result

	def get_ibe_sk(self,keywords):
		assert type(keywords) in [list,tuple]

		cipher = self.ciphers["keyword"]

		return [cipher.private_keygen(keyword) for keyword in keywords]

	def get_supported_attr_types(self):
		return tuple(self.__supported_attr_types)

    # Maps an attribute to one of those supported fields
	def set_attr(self,field,t):
		assert type(field) == str
		assert type(t) == str
		assert t in self.__supported_attr_types

		self.__mapped_attr[field] = t
