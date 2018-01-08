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
import Crypto
from time import time
import itertools
import timeit
import tqdm
from multiprocessing import Pool

#
datafile = open("synthetic_dataset.json")
dataset = json.load(datafile)

nMax = max(set([x["age"] for x in dataset]))
n = nMax+1
client = Client(Client.keygen())

client.set_attr("email","static")
client.set_attr("firstname","static")
client.set_attr("surname","static")
client.set_attr("country","static")
client.set_attr("age","index")
client.set_attr("text","static")
inames = ["age"]

s = SecMongo(add_cipher_param=pow(client.ciphers["h_add"].keys["pub"]["n"],2))
s.open_database("benchmark")
s.set_collection("encrypted")
s.drop_collection()

print "%d items were loaded" % len(dataset)

#
client.encrypt(dataset[0])

for i, _ in enumerate(dataset):
    dataset[i]["_id"] = i # Add an id
print "Documents loaded: %d" % len(dataset)

# Gen indexes
start = time()
for iname in inames:
    # Gen the index
    indexes_dataset = s.mem_ordered_build_index(dataset, iname, client)
    s.insert_mem_tree(indexes_dataset)
print "Indexes generated: %.2fs (%.2f doc/s)" % (time() - start, len(dataset)/(time() - start))


def encrypt_static_parallel(args):
    doc, client = args
    Crypto.Random.atfork()
    return client.encrypt(doc, skip_index = True)

start = time()
enc_dataset = []
p = Pool()
for result in tqdm.tqdm(p.imap_unordered(
    encrypt_static_parallel,
    itertools.izip(
        dataset,
        itertools.repeat(client)
        )), total=len(dataset)):
    enc_dataset.append(result)
p.close()
p.join()
p.terminate()
print "Encrypt: %.2fs (%.2f doc/s)" % (time() - start, len(dataset)/(time() - start))

def encrypted_query():
	return s.find(index=client.get_ctL(nMax), iname = "age")

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

unencrypted_client = MongoClient()
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
