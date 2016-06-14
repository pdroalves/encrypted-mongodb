#!/usr/bin/python
# coding: utf-8
import pymongo
from pymongo import MongoClient
import cipher.ibe as ibe
from cipher import paillier
from cipher import elgamal

class StopLookingForThings(Exception): pass

class SecMongo:
	ASCENDING = pymongo.ASCENDING
	DESCENDING = pymongo.DESCENDING

	client = None
	db = None
	collection = None
	
	keyword_attr = "keywords"

	__ciphers = {"keyword":None,"h_add":None,"h_mul":None}

	def __init__(self,add_cipher_param=None,url=None):
		assert url is None or type(url) == str

		# Connects to database
		if url:
			self.client = MongoClient(url)
		else:
			self.client = MongoClient()

		self.__ciphers["keyword"] = ibe.IBE()
		self.__ciphers["h_add"] = paillier.Paillier()
		self.__ciphers["h_add"].add_to_public_key("n2",add_cipher_param)
		self.__ciphers["h_mul"] = elgamal.ElGamal()

	def open_database(self,database):
		assert type(database) is str 
		self.db = self.client[database]


	def set_collection(self,collection):
		assert type(collection) is str 
		self.collection = self.db[collection]

	def find(self,keywords=[],range_selection=None,projection=None,sort=None):
		# Search by keyword or by range
		# This method expects something like:
		# 
		# fields = {
		#                "keywords":[Private_Key(msk,"batata"),Private_Key(msk,"amor")],
		#                "estradas.keywords":[Private_Key("bandeirantes,anhanguera")]
		#            }
		#            
		# for a simple selection by keywords.
		# 
		# For a selection by range, supposing that "age" is an attribute of type "range", it expects:
		# fields = {
		#               "age":{
		#                       "$gt":Enc(30),
		#                       "$lt":Enc(40)
		#                       }
		#           }
		#           
		#  To search for elements with an attribute named "age" with a value between 30 and 40
		#  
		#  The query MUST be encrypted

		# 
		# First we select by the most selective attribute type: range.
		# 

		# cursor = self.collection.find(projection=[attr for attr in query.keys()])
		if range_selection:
			cursor = self.collection.find(range_selection)
		else:
			cursor = self.collection.find()

		if sort:
			if cursor.count() > 0:
				cursor = cursor.sort(sort)

		if len(keywords) > 0:
			# Selection by keywords requires a linear search.
			for document in cursor:
				if self.__eval_search(	keywords,
										document[self.keyword_attr]
											): 
					yield self.collection.find_one({"_id":document["_id"]},projection=projection)
		else:
			for result in cursor:
				yield result
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
		self.collection.insert(doc)
		return

	def drop_collection(self):
		self.collection.drop()
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