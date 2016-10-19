#!/usr/bin/python
# coding: utf-8
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
import pymongo
from pymongo import MongoClient
from cipher import paillier
from cipher import elgamal
from crypto.pymodule.ore import ORE
# from crypto.ore import ORESMALL as ORE
from index.avltree import AVLTree
from index.indexnode import IndexNode
from bson.json_util import dumps
from bson.objectid import ObjectId
import json

class StopLookingForThings(Exception): pass

class SecMongo:
	ASCENDING = pymongo.ASCENDING
	DESCENDING = pymongo.DESCENDING

	client = None
	db = None
	collection = None
	
	__ciphers = {"index":None,"h_add":None,"h_mul":None}

	def __init__(self,add_cipher_param=None,url=None):
		assert url is None or type(url) == str

		# Connects to database
		if url:
			self.client = MongoClient(url)
		else:
			self.client = MongoClient()

		self.__ciphers["index"] = ORE
		self.__ciphers["h_add"] = paillier.Paillier()
		self.__ciphers["h_add"].add_to_public_key("n2",add_cipher_param)
		self.__ciphers["h_mul"] = elgamal.ElGamal()

	def open_database(self,database):
		assert type(database) is str 
		self.db = self.client[database]

	def set_collection(self,collection):
		assert type(collection) is str 
		self.collection = self.db[collection]
		self.index_collection = self.db["indexes-"+collection]

	def find(self,index=None,projection=None):
		if index is None:
			return self.collection.find()

		# Search by an index
		# This method expects an index value (the ctL)
		# 
		ctL = index # a
		#           
		#  To search for elements with an attribute named "age" with a value 
		#  between 30 and 40
		#  
		#  The query MUST be encrypted

		# Get the tree root
		node = self.index_collection.find_one({"root":"1"})
		while node is not None:
			ctR = node["ctR"] # b
			r = self.__ciphers["index"].compare(ctL,ctR)
			if r == 0:
				# Found
				# a == b
				return self.collection.find({"index":{"$in":node["index"]}})
			elif r == 1:
				# a > b
				node = self.index_collection.find_one({"_id":ObjectId(node["right"])})
			else:
				# a < b
				node = self.index_collection.find_one({"_id":ObjectId(node["left"])})
				assert r == -1
		return None
	# 
	# selection: a query in the same format required by find()
	# diff: A single dict in the format {operation:{field1:Enc(value1),field2:Enc((value2),...}}
	def update(self,selection,diff):
		# 
		# Select and update a set of entries 
		#
		operation = diff.keys()[0]
		output = []
		s = self.find(selection,projection=["_id"] + diff[operation].keys())

		if operation in ["$inc","$dec"]:
			field_kind = "h_add"
		
			cipher = self.__ciphers[field_kind]
			for document in s:
				for attribute in diff[operation]:
					A = diff[operation][attribute]
					B = document[attribute]

					result = cipher.h_operation(A,B)

					output.append( self.collection.update({"_id":document["_id"]},{"$set":{attribute:result}}) )
		elif operation == "$set":
			output = [self.collection.update({"_id":x["_id"]},diff) for x in s]
		else:
			raise ValueError()

		return output

	def insert(self,doc):
		return self.collection.insert(doc)

	def insert_tree(self,node,data_indexes):
		if node is None:
			return None
		# Down the tree from its root, build a index-document and add to the database
		new_doc = {	"index": node.me._id, # pointer to data
					"ctR": node.me.value[1], # value used for selection
					"left": self.insert_tree(node.left,data_indexes), 
					"right": self.insert_tree(node.right,data_indexes) 
					}
		if new_doc["left"]:
			new_doc["left"] = new_doc["left"].inserted_id
		if new_doc["right"]:
			new_doc["right"] = new_doc["right"].inserted_id
		# print json.dumps(new_doc,4)
		return self.index_collection.insert_one(new_doc)		

	def insert_indexed(self,roottree,data):
		# Receives AVL tree that index a list of elements Lewi's scheme
		# 
		# Each node contains a pair composed by the right side of a ciphertext and
		# the index of a related element in the list data (IndexNode)
		# 
		assert isinstance(roottree, AVLTree)
		assert type(data) in (list,tuple)

		# Adds data to the database and keep the ids
		data_indexes = []
		for i,item in enumerate(data):
			item["index"] = i
			data_indexes.append(self.insert(item))

		# Add indexes
		root = self.insert_tree(roottree,data_indexes)
		# Add a tag to the root node
		self.index_collection.update({"_id":root.inserted_id},{"$set":{"root":"1"}})

		return root

	def drop_collection(self):
		self.collection.drop()
		self.index_collection.drop()
		return

	###########################################################################
    # 	Receives a list of keywords and verifies if any can be decrypted by some 
    # sk in a list
    # 
    # 	The list of sks may have two levels. The first level represents a bitwise
    # AND, while the second one represents a bitwise OR.
    # 
    # i.e.
    # 
    # ["potatoes","hobbit",["frodo","sam"]]
    # 
    # this query should return results that contains ("frodo" or "sam") and "potatoes" and "hobbit" 
    # 

	def __eval_search(self,queries,keywords):
		assert type(queries) in [list,tuple]
		assert type(keywords) in [str,int,long,list,tuple]

		for query in queries:
			sk = query	

			if type(sk) in [list,tuple]:
				#OR
				try:
					for orsk in query:
						if self.__exists(orsk,keywords):
							raise StopLookingForThings()
					return False
				except StopLookingForThings:
					return True
					continue
			else:
				# AND
				if not self.__exists(sk,keywords):
					return False
					continue

		return True

	# Receives a list of keywords and a sk. 
	# Return True if there is any keyword in the list that matches with the sk.
	def __exists(self,sk,keywords):
		if all(type(keywords) in [list,tuple] for keywords in keywords):
			for keyword in keywords:
				# Must exist at least one
				pt = self.__ciphers["keyword"].decrypt(sk,keyword)
				if pt in ([1],(1,)):
					return True
		else:
			keyword = keywords
			pt = self.__ciphers["keyword"].decrypt(sk,keyword)
			if pt in ([1],(1,)):
				return True
		return False
