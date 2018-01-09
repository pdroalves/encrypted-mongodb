#!/usr/bin/python
# coding:  utf-8
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
#

import sys
import linecache
import json
import re
import time
import csv
import itertools
import Crypto
import gc
import tqdm
import calendar
import tempfile

sys.path.append("../src/")
from optparse import OptionParser
from pymongo import MongoClient
from client import Client
from secmongo import SecMongo
from bson.json_util import dumps
from secmongo.index.avltree import AVLTree
from secmongo.index.indexnode import IndexNode
from secmongo.index.encryptednode import EncryptedNode
from os import walk
from multiprocessing import Pool
from datetime import datetime
from pymongo.errors import BulkWriteError
from bson.objectid import ObjectId
from bson import json_util
from itertools import chain,islice

def load_data(inputfile):
    # Opens training dataset, read line-by-line and append to a list
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

##############################
# The call for this script must have a single parameter with the path to the 
# dataset
##############################

def main():
    ##############################
    # Parse input parameters
    parser = OptionParser()
    parser.add_option("-p", "--path", dest="path",
                      help="the path to the dataset", metavar="FILE")
    parser.add_option("-u", "--url", dest="url",
                      help="url to the MongoDB server", metavar="FILE")
    parser.add_option("-k", "--keys", dest="okeys",
                      help="where the keys shall be stored", metavar="FILE")

    (options, args) = parser.parse_args()

    assert options.path is not None
    assert options.url is not None
    okeys = "keys.json" if options.okeys is None else options.okeys
    ##############################
    # Path to data
    # 
    path = options.path

    print "Starting now."
    print "Dataset path: %s" % path

    docs = [] # plaintext docs
    enc_docs = [] # encrypted docs
    indexes_enc_docs = [] # indexes
        
    ##############################
    # Setup client
    start = time.time()
    client = Client(Client.keygen())
    client.ciphers["h_add"].rating_cts = [client.ciphers["h_add"].encrypt(m) for m in range(6)]
    with open(okeys, "wb") as f:
        print client.keys
        json.dump(client.keys, f)    
        print "Keys exported to %s" % okeys

    ##############################
    # Attributes should be classified using add_attr(). The encrypted document 
    # will contain the ciphertext related to each of these atributes.
    # There is no relation with the indexing itself.
    client.add_attr(attribute = "static", name = "movieid")
    client.add_attr(attribute = "static", name = "customerid")
    client.add_attr(attribute = "static", name = "rating")
    client.add_attr(attribute = "static", name = "date")
    client.add_attr(attribute = "index", name = "movieid")
    client.add_attr(attribute = "index", name = "date")
    client.add_attr(attribute = "index", name = "rating")
    client.add_attr(attribute = "h_add", name = "rating")

    # 
    # Encrypted documents with this setup will contain AES ciphertexts for 
    # movieid, customerid, rating, and date; ORE_lewi ciphertext for date and
    # rating; and a Paillier ciphertex for rating.
    # 
    ##############################
    # inames will be used for indexing
    inames = ["customerid", "movieid", "date"]

    ##############################
    ##############################
    # Setup the MongoDB driver
    print "Establishing connection to the database... ",
    s = SecMongo(url=options.url, add_cipher_param=pow(client.ciphers["h_add"].keys["pub"]["n"], 2))
    s.open_database("netflix")
    s.set_collection("data2")
    s.drop_collection()
    s.load_scripts()
    print "Done"

    ##############################
    # Load the unencrypted dataset to memory
    # The dataset is segmented in chunks of size N before being appended to docs
    print "Loading documents...",
    N = 100000
    start = time.time()
    for chunk in load_directory(path,N):
        docs.extend(chunk)
        if len(docs) > 100000:
            break
    print "Load: %.2fs" % (time.time() - start)

    # Add an id to each doc
    for i, _ in enumerate(docs):
        docs[i]["_id"] = i # Add an id
    print "Documents loaded: %d" % len(docs)

    ##############################
    # Generate indexes
    print "Generating indexes..."
    start = time.time()
    for iname in inames:
        # build the index for each iname on memory and then inserts on the DB
        indexes_docs = s.mem_ordered_build_index(docs, iname, client)
        s.insert_mem_tree(indexes_docs)
    print "Done"
    print "Indexes generated: %.2fs (%.2f doc/s)" % (time.time() - start, len(docs)/(time.time() - start))

                
    ##############################
    # Encrypt
    def chunks(iterable, size=100000):
            iterator = iter(iterable)
            for first in iterator:
                yield chain([first], islice(iterator, size - 1))

    start = time.time()
    p = Pool()
    N = 100000
    print "Encrypting..."
    for c in chunks(docs, size = N):
        # Encrypt the dataset in chunks of size N and inserts to the DB.
        # Doing this way we reduce the required memory space
    	enc_docs = []
    	for result in tqdm.tqdm(p.imap_unordered(
    	    encrypt_static_parallel,
    	    itertools.izip(
    	        c,
    	        itertools.repeat(client)
    	        )), total=min(N, len(docs))):
    	    enc_docs.append(result)

    	# Insert ciphertexts to the DB
    	try:
    		s.insert_many(enc_docs)
    	except BulkWriteError as exc:
    		print exc.details
    		exit(1)
    	print "Chunk processed."
    print "Done"
    print "Encrypt: %.2fs (%.2f doc/s)" % (time.time() - start, len(docs)/(time.time() - start))
    p.close()
    p.join()
    p.terminate()

    print "Insert encrypt docs: %.2fs (%.2f doc/s)" % (time.time() - start, len(docs)/(time.time() - start))

if __name__ == "__main__":
    main()