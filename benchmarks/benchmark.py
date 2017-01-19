#!/usr/bin/python
import json
from client import Client
from secmongo import SecMongo
from secmongo.index.indexnode import IndexNode
from secmongo.index.avltree import AVLTree
from pymongo import MongoClient
from time import time
import timeit
import generate_dataset as genDataset

import pytest

url = "mongodb://localhost:27017"

# ######################################
# AUX
# #####################################
def build_index(dataset):
	root = AVLTree([dataset[0]["age"],0],nodeclass=IndexNode)
	for i,doc in enumerate(dataset[1:]):
		root = root.insert([doc["age"],i+1])

	# assert it is correct
	for data in dataset:
		assert root.find(data["age"])
	return root

def load_encrypted_data(s, client, dataset):
	# Build a index
	index = build_index(dataset)
	index.encrypt(client.ciphers["index"])
	encrypted_dataset = []
	for data in dataset:
		encrypted_dataset.append(client.encrypt(data))

	s.insert_indexed(index,encrypted_dataset)

def encrypted_query(s, client, index):
	return s.find(index=index)

def load_data(collection, dataset):
	count = 0
	start = time()
	for entry in dataset:
		if (count % 1000) == 0:
			# 
			# print "%d - %f elements/s" % (count, 1000/(time()-start))
			start = time()
		count = count + 1
		collection.insert(entry)

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

def unencrypted_query(collection, nMax):
	return collection.find_one({"age":nMax})


# ######################################
# TESTS
# #####################################

def test_encrypted(benchmark):

	#
	datafile = open("synthetic_dataset.json")
	dataset = json.load(datafile)

	nMax = max(set([x["age"] for x in dataset]))
	n = nMax+1
	print("Maximum integer supported by the ORE cryptosystem: %d" % n)
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

	print("%d items were loaded" % len(dataset))

	#
	client.encrypt(dataset[0])
	dataset.sort(key=lambda x: x["age"])

	# load
	load_encrypted_data(s, client, dataset)

	benchmark(encrypted_query, s , client , client.get_ctL(nMax))

def test_unencrypted(benchmark):
	#
	datafile = open("synthetic_dataset.json")
	dataset = json.load(datafile)
	
	nMax = max(set([x["age"] for x in dataset]))
	n = nMax+1

	unencrypted_client = MongoClient(url)
	db = unencrypted_client["benchmark"]
	collection = db["unencrypted"]
	collection.drop()

	load_data(collection,dataset)	#

	benchmark(unencrypted_query, collection, nMax)