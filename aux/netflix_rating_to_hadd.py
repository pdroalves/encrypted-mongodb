#!/usr/bin/python
# coding:  utf-8
from pymongo import MongoClient
from client import Client
from secmongo import SecMongo
from bson.json_util import dumps
from secmongo.index.avltree import AVLTree
from secmongo.index.indexnode import IndexNode
from secmongo.index.encryptednode import EncryptedNode
import linecache
import json
import re
import time
import csv
from os import walk
import sys
from multiprocessing import Pool
import itertools
import Crypto
import gc
import tqdm
import calendar
from datetime import datetime

import tempfile
from bson.objectid import ObjectId
from bson import json_util

enc_docs = []
indexes_enc_docs = []
docs = []
    
##############################
# Setup client
start = time.time()
client = Client(Client.keygen())
print client.keys
client.add_attr(attribute = "static", name = "movieid")
client.add_attr(attribute = "static", name = "customerid")
client.add_attr(attribute = "static", name = "rating")
client.add_attr(attribute = "static", name = "date")
client.add_attr(attribute = "index", name = "date")
client.add_attr(attribute = "index", name = "rating")
client.add_attr(attribute = "h_add", name = "rating")

##############################
# Setup the MongoDB driver
s = SecMongo(add_cipher_param=pow(client.ciphers["h_add"].keys["pub"]["n"], 2))
s.open_database("netflix")
s.set_collection("data")

client.ciphers["h_add"].rating_cts = [client.ciphers["h_add"].encrypt(x) for x in range(6)]

# Rating
count = 0
k = 0
N = s.collection.find().count()
start = time.time()
bulk = s.collection.initialize_unordered_bulk_op()
for i in s.collection.find():
	try:
		# dec_value = client.ciphers["h_add"].decrypt(i["rating"]["h_add"])
		# if dec_value in range(6):
			# print "We are good."
			# pass
		# else:
		value = int(client.ciphers["static"].decrypt(i["rating"]["static"]))
		assert value in range(6)
		bulk.find({"_id":i["_id"]}).update({"$set":{"rating.h_add":client.ciphers["h_add"].encrypt(value)}})
		count = count + 1
		if count % 1000 == 0 and count > 0:
			bulk.execute()
			bulk = s.collection.initialize_unordered_bulk_op()
			print "%d / %d - %.1f docs/s" % (count, N, (float(count - k))/(time.time()-start))
			k = count
			start = time.time()
	except Exception as e:
		print "Exception: %s" % e
		pass
