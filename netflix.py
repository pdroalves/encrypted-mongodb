#!/usr/bin/python
# coding:  utf-8
# ##########################################################################
##########################################################################
#
# mongodb-secure
# Copyright (C) 2017, Pedro Alves and Diego Aranha
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
from pymongo.errors import BulkWriteError
import tempfile
from bson.objectid import ObjectId
from bson import json_util

from itertools import chain,islice

def load_data(inputfile):
    # Opens training dataset, read line-by-line and write in a list
    docs = list()
    with open(inputfile, "r") as f:
        movieid = int(f.readline().split(":")[0])
        reader = csv.reader(f)
        for rating in reader:
            docs.append({
                "movieid": movieid,
                "customerid": int(rating[0]),
                "rating": int(rating[1]),
                "date": calendar.timegm(datetime.strptime(rating[2], "%Y-%m-%d").timetuple())
                })

    return docs              

def load_directory(path, N):
    # Loads all files in a directory
    (_, _, filenames) = walk(path).next()
    data = list()

    p = Pool()
    for result in tqdm.tqdm(p.imap_unordered(
            load_data,
            # [path + "/" + filename for filename in filenames]), 
            [path + "/" + filename for filename in filenames[:1000]]), 
        total=len(filenames)):
        data.extend(result)

        if len(data) >= N:
            yield data
            data = []
    if len(data) > 0:
        yield data
        del data
    p.close()
    p.join()
    p.terminate()

def encrypt_static_parallel(args):
    doc, client = args
    Crypto.Random.atfork()
    return client.encrypt(doc)

enc_docs = []
indexes_enc_docs = []
docs = []
    
##############################
# Setup client
start = time.time()
client = Client(Client.keygen())
client.ciphers["h_add"].rating_cts = [client.ciphers["h_add"].encrypt(m) for m in range(6)]
print client.keys
# Attributes should be classified using add_attr(). This action will imply in
# ciphertexts stored with all tagged attributes. There is no relation with
# the indexing itself.
client.add_attr(attribute = "static", name = "movieid")
client.add_attr(attribute = "static", name = "customerid")
client.add_attr(attribute = "static", name = "rating")
client.add_attr(attribute = "static", name = "date")
client.add_attr(attribute = "index", name = "date")
client.add_attr(attribute = "index", name = "rating")
client.add_attr(attribute = "h_add", name = "rating")
# inames will be used for indexing
inames = ["customerid", "movieid", "date"]

##############################
# Path to data
# assert len(sys.argv) == 2
# path = sys.argv[1]
path = "/home/pdroalves/doutorado/netflix_dataset/training_set"

print "Starting now."
print "Training set path: %s" % path

##############################
# Load plaintext
                                     # 
##############################
# Setup the MongoDB driver
s = SecMongo(url="gtxtitan", add_cipher_param=pow(client.ciphers["h_add"].keys["pub"]["n"], 2))
s.open_database("netflix")
s.set_collection("data")
s.drop_collection()
s.load_scripts()

# Load
N = 100000
start = time.time()
for chunk in load_directory(path,N):
    docs.extend(chunk)

print "Load: %.2fs" % (time.time() - start)
for i, _ in enumerate(docs):
    docs[i]["_id"] = i # Add an id
print "Documents loaded: %d" % len(docs)

# Gen indexes
start = time.time()
for iname in inames:
    # Gen the index for iname
    indexes_docs = s.mem_ordered_build_index(docs, iname, client)
    s.insert_mem_tree(indexes_docs)
print "Indexes generated: %.2fs (%.2f doc/s)" % (time.time() - start, len(docs)/(time.time() - start))

def chunks(iterable, size=100000):
        iterator = iter(iterable)
        for first in iterator:
            yield chain([first], islice(iterator, size - 1))
            
# Encrypt
start = time.time()
p = Pool()
N = 100000
for c in chunks(docs, size = N):
	enc_docs = []
	for result in tqdm.tqdm(p.imap_unordered(
	    encrypt_static_parallel,
	    itertools.izip(
	        c,
	        itertools.repeat(client)
	        )), total=min(N, len(docs))):
	    enc_docs.append(result)

	target_customer_id = docs[0]["customerid"]

	print enc_docs[0]
	# Insert ciphertexts
	try:
		s.insert_many(enc_docs)
	except BulkWriteError as exc:
		print exc.details
		exit(1)
	print "Chunk processed."
print "Encrypt: %.2fs (%.2f doc/s)" % (time.time() - start, len(docs)/(time.time() - start))
p.close()
p.join()
p.terminate()

print "Insert encrypt docs: %.2fs (%.2f doc/s)" % (time.time() - start, len(docs)/(time.time() - start))

##############################
# Queries
import json
def parse(doc):
    parsed_doc = {}
    keys = doc.keys()
    for key in keys:
        if key == "_id":
            parsed_doc[key] = doc[key]
        elif "static" in doc[key]:
            parsed_doc[key] = doc[key]["static"]
    return parsed_doc

print "Customer %d: " % target_customer_id
projection = ["movieid", "rating", "customerid", "date"]
result = [client.decrypt(x) for x in s.find(client.get_ctL(target_customer_id), iname="customerid", projection = projection)]
print "%d results" % len(result)
for r in result:
    print json.dumps(parse(r), indent=4)
