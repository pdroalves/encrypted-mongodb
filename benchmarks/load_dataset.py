#!/usr/bin/python
# coding: utf-8
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
# This routine loads a dataset from a file named "synthetic_dataset.json" and generated
# by the script generate_dataset.py.
# 
# After that, a database named "benchmark" is created as well as two collections 
# named "encrypted" and "unencrypted". The dataset is inserted encrypted to the 
# former and unencrypted in the latter and speed results are printed.
# 

import json
from client import Client
from secmongo import SecMongo
from pymongo import MongoClient
from time import time
from index.indexnode import IndexNode
from index.avltree import AVLTree
import timeit

url = "192.168.1.201"

#
datafile = open("synthetic_dataset.json")
dataset = json.load(datafile)

nMax = max(set([x["age"] for x in dataset]))
n = nMax+1
print "Maximum integer supported by the ORE cryptosystem: %d" % n
client = Client(Client.keygen(),n=n)

client.set_attr("email","static")
client.set_attr("firstname","static")
client.set_attr("surname","static")
client.set_attr("country","static")
client.set_attr("age","index")
client.set_attr("text","static")

s = SecMongo(url=url, add_cipher_param=pow(client.ciphers["h_add"].keys["pub"]["n"],2))
s.open_database("benchmark")
s.set_collection("encrypted")
s.drop_collection()

print "%d items were loaded" % len(dataset)

#
client.encrypt(dataset[0])

dataset.sort(key=lambda x: x["age"])

def build_index(dataset):
	root = AVLTree([dataset[0]["age"],0],nodeclass=IndexNode)
	for i,doc in enumerate(dataset[1:]):
		root = root.insert([doc["age"],i+1])

	# assert it is correct
	for data in dataset:
		assert root.find(data["age"])
	return root

def load_encrypted_data():
	# Build a index
	index = build_index(dataset)
	index.encrypt(client.ciphers["index"])
	encrypted_dataset = []
	for data in dataset:
		encrypted_dataset.append(client.encrypt(data))

	s.insert_indexed(index,encrypted_dataset)

diff = timeit.timeit("load_encrypted_data()",setup="from __main__ import load_encrypted_data",number=1)
print "Encrypted data loaded in %fs - %f elements/s" % (diff,len(dataset)/(diff))

def encrypted_query():
	return s.find(index=client.get_ctL(nMax))

diff = timeit.timeit("encrypted_query()",setup="from __main__ import encrypted_query",number=100)
print "Encrypted query in %fs" % (diff)

def load_data():
	count = 0
	start = time()
	for entry in dataset:
		if (count % 1000) == 0:
			# 
			# print "%d - %f elements/s" % (count, 1000/(time()-start))
			start = time()
		count = count + 1
		collection.insert(entry)

unencrypted_client = MongoClient(url)
db = unencrypted_client["benchmark"]
collection = db["unencrypted"]
collection.drop()

diff = timeit.timeit("load_data()",setup="from __main__ import load_data",number=1)
print "Unencrypted data loaded in %fs - %f elements/s" % (diff,len(dataset)/(diff))

# Create index
collection.create_index([("age", SecMongo.ASCENDING)])
def query(predicate,projection):
	result = []
	for x in s.find(client.get_ibe_sk(predicate),projection=projection):
		result.append(x)
	return result

def query_range(predicate,projection):
	result = []
	for x in s.find(sort=[("age",SecMongo.DESCENDING)],projection=projection):
		result.append(x)
	return result

def unencrypted_query():
	return collection.find_one({"age":nMax})
diff = timeit.timeit("unencrypted_query()",setup="from __main__ import unencrypted_query",number=100)
print "Unencrypted query in %fs" % (diff)
