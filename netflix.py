#!/usr/bin/python
# coding:  utf-8

from client import Client
from secmongo import SecMongo
from bson.json_util import dumps
from secmongo.index.avltree import AVLTree
from secmongo.index.encryptednode import EncryptedNode
import linecache
import json
import re
import time
import csv
from os import walk
from multiprocessing.pool import ThreadPool
from os import listdir 
import csv


def load_data(inputfile):
    # Opens training dataset, read line-by-line and write in a list
    docs = []
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
    print "%s - Done" % inputfile
    return docs

def load_directory(path):
    # Loads all files in a directory
    p = ThreadPool()
    data = p.map(load_data, [path + x for x in listdir(path)])
    p.close()
    p.join()
    return data
    

# Setup client
client = Client(Client.keygen())
print client.keys
client.set_attr("movieid", "static")
client.set_attr("customerid", "index")
client.set_attr("rating", "static")
client.set_attr("date", "static")

# Setup the MongoDB driver
s = SecMongo(add_cipher_param=pow(client.ciphers["h_add"].keys["pub"]["n"], 2))
s.open_database("test_sec")
s.set_collection("netflix")
s.drop_collection()

print("Loading...")
start = time.time()
docs = load_directory("../dataset/training_set/")
print("Loading time: ", time.time() - start)

# print("Inserting...")
# start = time.time()
# while len(docs) > 0:
#     doc = docs.pop()

# print("Insert time: ", time.time() - start)

