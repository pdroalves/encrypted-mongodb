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
from random import randint 

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
s = SecMongo(url="gtxtitan", add_cipher_param=pow(client.ciphers["h_add"].keys["pub"]["n"], 2))
s.open_database("netflix")
s.set_collection("data")

# Rating
count = 0
k = 0
N = s.collection.find().count()
start = time.time()
bulk = s.collection.initialize_unordered_bulk_op()
for i in s.collection.find():
	if "index" in i["date"].keys():
		pass
	else:
		value = client.ciphers["static"].decrypt(i["date"]["static"])
		# print value
		bulk.find({"_id":i["_id"]}).update({"$set":{"date.index":client.get_ctL(value)}})

	count = count + 1
	if count % 1000 == 0 and count > 0:
		try:
			bulk.execute()
		except Exception as e:
			print e
			pass

		bulk = s.collection.initialize_unordered_bulk_op()
		print "%d / %d - %.1f docs/s" % (count, N, (float(count - k))/(time.time()-start))
		k = count
		start = time.time()
