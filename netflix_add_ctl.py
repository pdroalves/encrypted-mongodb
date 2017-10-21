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
client.set_attr("movieid", "index")
client.set_attr("customerid", "index")
client.set_attr("rating", "static")
client.set_attr("date", "static")

##############################
# Setup the MongoDB driver
s = SecMongo(add_cipher_param=pow(client.ciphers["h_add"].keys["pub"]["n"], 2))
s.open_database("netflix")
s.set_collection("data")

# # Date
# count = 0
# N = s.index_collection.find().count()
# for i in s.index_collection.find():
# 	sample = i["references"].pop()
# 	value = client.decrypt(s.collection.find_one({"_id":sample}))["date"]
# 	s.index_collection.update_one({"_id":i["_id"]},{"$set":{"ctL":client.get_ctL(value)}})
# 	count = count + 1
# 	print "%d / %d" % (count, N)

def is_int(s):
    try:
        int(s)
        return True
    except ValueError:
        return False

            g_m__n2 = pow(g,m,n2)

        c = g_m__n2*pow(r,n,n2) % n2

# Rating
count = 0
k = 0

g = client.ciphers["h_add"].keys["pub"]["g"]
n = client.ciphers["h_add"].keys["pub"]["n"]
n2 = n*n
r_n_n2 = pow(42,n,n2) % n2
ct = [pow(g,int(value),n2)*r_n_n2 % n2 for value in range(1,6)]

N = s.collection.find().count()
start = time.time()
bulk = s.collection.initialize_unordered_bulk_op()
for i in s.collection.find():
	if is_int(i["rating"]):
		pass
	else:
		value = client.decrypt(i)["rating"]
		bulk.find({"_id":i["_id"]}).update({"$set":{"rating":str(ct[int(value)])}})
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
