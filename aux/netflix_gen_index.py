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
client.set_attr("rating", "h_add")
client.set_attr("date", "h_add")
inames = ["rating"]

##############################
# Setup the MongoDB driver
s = SecMongo(add_cipher_param=pow(client.ciphers["h_add"].keys["pub"]["n"], 2))
s.open_database("netflix")
s.set_collection("data")

# 
docs = [client.decrypt(x) for x in s.collection.find(projection={"_id":1, "rating":1})]
docs = [{"_id":x["_id"], "rating":int(x["rating"])} for x in docs]

# Gen indexes
start = time.time()
for iname in inames:
    # Gen the index
    indexes_docs = s.mem_ordered_build_index(docs, iname, client)
    s.insert_mem_tree(indexes_docs)
    del indexes_docs
print "Indexes generated: %.2fs (%.2f doc/s)" % (time.time() - start, len(docs)/(time.time() - start))

