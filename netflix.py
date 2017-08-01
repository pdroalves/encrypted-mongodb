#!/usr/bin/python
# coding:  utf-8

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
                "date": rating[2]
                })

    return docs              

def load_directory(path, driver, client):
    # Loads all files in a directory
    (_, _, filenames) = walk(path).next()
    data = list()
    for i, filename in enumerate(filenames[:100]):
    # for i, filename in enumerate(filenames[:5]):
        print "Remaining: %d/%d, " % (len(filenames) - i, len(filenames))
        start = time.time()
        data.extend(load_data(path + "/" + filename))
        diff = time.time() - start
        print "done in %ds" % (diff)

    return data

def encrypt(args):
    doc, [client, inames] = args
    Crypto.Random.atfork()

    enc_doc = client.encrypt(doc)
    return [enc_doc] + [[(client.ciphers["index"].encrypt(doc[iname]), iname) for iname in inames]]
    

# Setup client
client = Client(Client.keygen())
print client.keys
client.set_attr("movieid", "index")
client.set_attr("customerid", "index")
client.set_attr("rating", "index")
client.set_attr("date", "static")
inames = ["customerid","movieid","rating"]

# Setup the MongoDB driver
s = SecMongo(add_cipher_param=pow(client.ciphers["h_add"].keys["pub"]["n"], 2))
s.open_database("test_sec")
s.set_collection("netflix")
# s.drop_collection()

# # assert len(sys.argv) == 2
# # path = sys.argv[1]
# path = "/home/pdroalves/doutorado/netflix_dataset/training_set"

# print "Starting now."
# print "Training set path: %s" % path

# start = time.time()
# docs = load_directory(path, s, client)
# print("Loading time: ", time.time() - start)

##############################
# Encrypt data

# p = Pool()
# start = time.time()
# enc_docs = p.map(
#     encrypt,
#     itertools.izip(
#         docs,
#         itertools.repeat([client, inames])
#         )
#     )
# p.close()
# p.join()


# diff = time.time() - start
# print "Encryption time for %d docs: %f (%f doc/s)" % (len(enc_docs), diff, len(enc_docs)/diff)
#############################3
# Encrypt indexes
def build_index(docs, iname):
    # import pdb;pdb.set_trace()
    root = AVLTree([docs[0][iname],0],nodeclass=IndexNode)
    for i,doc in enumerate(docs[1:]):
        root = root.insert([doc[iname],i+1])
    return root

def encrypt_index(args):
    index, client = args
    index.encrypt(client.ciphers["index"])

# Build a index
# # start = time.time()
# # indexes = [build_index(docs, iname) for iname in inames]
# # diff = time.time() - start
# # print "Building indexes time for %d docs per index: %f (%f doc/s)" % (len(enc_docs), diff, len(inames)*len(enc_docs)/diff)

# del docs
# docs = None
# gc.collect()

# start = time.time()
# # p.map(encrypt_index, itertools.izip(indexes, itertools.repeat(client)))
# for index in indexes:
#     index.encrypt(client.ciphers["index"])
# diff = time.time() - start
# print "Encrypting indexes time for %d docs: %f (%f doc/s)" % (len(enc_docs), diff, len(enc_docs)/diff)

# #############################3
# # Insert indexes
# # 
# start = time.time()
# for iname, index in zip(inames, indexes):
#     s.insert_indexed(index, [x[0] for x in enc_docs], iname)
# diff = time.time() - start
# print "Inserting time for %d docs: %f (%f doc/s)" % (len(enc_docs), diff, len(enc_docs)/diff)
# 

# print("Starting now.")
# start = time.time()
# for i, pack in enumerate(enc_docs):
#     print "%d / %d " % (i, len(enc_docs))
#     enc_doc = pack[0]
#     inserted_doc = s.insert(enc_doc)
#     for iname_pack in pack[1]:
#         value, iname = iname_pack
#         # print iname
#         node = EncryptedNode(value, inserted_doc)
#         s.insert_index(node, iname)

import json

print "Customer 752642: "
# Expect to return 30 items
projection = ["movieid", "rating"]
result = [client.decrypt(x) for x in s.find(client.get_ctL(752642), iname="customerid", projection = projection)]
print "%d results" % len(result)
for r in result:
    r.pop("_id")
    print json.dumps(r, indent=4)

print "Movie 2808: "
projection = ["customerid", "rating", "date"]
result = [client.decrypt(x) for x in s.find(client.get_ctL(2808), iname="movieid", projection = projection)]
for r in result:
    r.pop("_id")
    print json.dumps(r, indent=4)

print "Movies with rating 5:"
projection = ["movieid"]
result = [client.decrypt(x) for x in s.find(client.get_ctL(5), iname="rating", projection = projection)]
for r in result:
    r.pop("_id")
    print json.dumps(r, indent=4)
