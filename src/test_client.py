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

def parse(docs):
    for i, doc in enumerate(docs):
        keys = doc.keys()
        for key in keys:
            if key == "_id":
                continue
            elif "static" in doc[key]:
                docs[i][key] = doc[key]["static"]
            else:
                docs[i].pop(key)
    return docs


def main():
    #
    # Input data
    #
    docs = [
        {
            "name": "Jon Snow",
            "age":  18,
            "height": 10,
            "address": "Castle Black, over a table",

        },
        {
            "name": "Eddard Stark",
            "age":  40,
            "height": 10,
            "address": "King's landing, in a spear",
        },
        {
            "name": "Catherine Stark",
            "age":  34,
            "height": 10,
            "address": "Hell, 123",
        },
        {
            "name": "Rob Stark",
            "age":  20,
            "height": 10,
            "address": "Hell, 124",
        },
        {
            "name": "Aria Stark",
            "age":  12,
            "height": 10,
            "address": "Braavos",
        },
        {
            "name": "Sansa Stark",
            "age":  16,
            "height": 2,
            "address": "North",
        },
        {
            "name": "Theon Greyjoy",
            "age":  19,
            "height": 10,
            "address": "No Dick's land",
        },
        {
            "name": "Tywin Lannister",
            "age":  55,
            "height": 10,
            "address": "King's landing",
        },
        {
            "name": "Tyrion lannister",
            "age": 38,
            "height": 5,
            "address": "Dragonstone"
        },
        {
            "name": "Cersei Lannister",
            "age":  35,
            "height": 20,
            "address": "King's landing",
        },
        {
            "name": "Jaime Lannister",
            "age":  35,
            "height": 20,
            "address": "King's landing",
        },
        {
            "name": "Robert Baratheon",
            "age":  41,
            "height": 30,
            "address": "King's landing",
        },
        {
            "name": "Joffrey Baratheon",
            "age":  17,
            "height": 30,
            "address": "King's landing",
        },
        {
            "name": "Lady Melissandre",
            "age":  201,
            "height": 30,
            "address": "Castle Black, naked",
        }
    ]
    # Setup client
    client = Client(Client.keygen())
    print client.keys
    # Attributes should be classified using add_attr(). This action will imply in
    # ciphertexts stored with all tagged attributes. There is no relation with
    # the indexing itself.
    client.add_attr(name = "name", attribute = "static")
    client.add_attr(name = "address", attribute = "static")
    client.add_attr(name = "age", attribute = "static")
    client.add_attr(name = "age", attribute = "index")
    client.add_attr(name = "height", attribute = "static")
    client.add_attr(name = "height", attribute = "index")
    # inames will be used to build the indexing
    inames = ["age", "height"]

    # Setup the MongoDB driver
    s = SecMongo(add_cipher_param=pow(client.ciphers["h_add"].keys["pub"]["n"],
                                      2),
                 url='gtxtitan')
    s.open_database("test_sec")
    s.set_collection("gameofthrones")
    s.drop_collection()

    # s.load_scripts()

    print("Starting now.")
    start = time.time()
    enc_docs = []
    indexes_enc_docs = []
    for i, doc in enumerate(docs):
        enc_doc = client.encrypt(doc)
        print json.dumps(client.decrypt(enc_doc), indent=4)
        enc_docs.append(enc_doc)
    for i, _ in enumerate(enc_docs):
        enc_docs[i]["_id"] = i # Add an id
                               # 
    # Unload enc_docs to the DB
    start = time.time()
    s.collection.insert_many(
        enc_docs,
        ordered = False,
        bypass_document_validation = True)
    end = time.time()
    print "Inserted in the database: %.2f docs/s" % (len(enc_docs)/(end-start))

    ##############################
    # Build the index

    print("Creating the indexes")
    count = 0 
    start = time.time()
    p_time = start
    for iname in inames:
        print "Will build for %s: " % (iname)
        iname_index = s.mem_enc_ordered_build_index(enc_docs, iname)
        print "Done."

        print "Will insert...",
        s.insert_mem_tree(iname_index)
        print "Done."

        del iname_index

    diff = time.time() - start
    print "Indexes created for %d docs: %f (%f doc/s)" % (len(inames)*len(indexes_enc_docs), diff, len(indexes_enc_docs)/diff)

    print "Insert time: ", time.time() - start
    ##############################
    # Queries

    docs.sort()

    print "\nIt's query time! \o/\n"
    print "People of 35 years old:",
    results = [client.decrypt(doc) for doc in s.find(index=client.get_ctL(35), iname = "age", relationship = 0)]
    results = parse(results)
    results = [dict(t) for t in set([tuple(d.items()) for d in results])]
    results.sort()
    print [x["name"] for x in results] == [x["name"] for x in docs if x["age"] == 35]

    # "I want all records such that 35 is lower than"
    print "People older than 35 years old:",
    results = [client.decrypt(doc) for doc in s.find(index=client.get_ctL(35), iname = "age", relationship = -1)]
    results = parse(results)
    results = [dict(t) for t in set([tuple(d.items()) for d in results])]
    results.sort()
    print set([x["name"] for x in results]) == set([x["name"] for x in docs if x["age"] > 35])
    
    print "People younger than 35 years old:",
    results = [client.decrypt(doc) for doc in s.find(index=client.get_ctL(35), iname = "age", relationship = 1)]
    results = parse(results)
    results = [dict(t) for t in set([tuple(d.items()) for d in results])]
    results.sort()
    print set([x["name"] for x in results]) == set([x["name"] for x in docs if x["age"] < 35])

    print "People of height 10:",
    results = [client.decrypt(doc) for doc in s.find(index=client.get_ctL(10), iname = "height", relationship = 0)]
    results = parse(results)
    results = [dict(t) for t in set([tuple(d.items()) for d in results])]
    results.sort()
    print set([x["name"] for x in results]) == set([x["name"] for x in docs if x["height"] == 10])

    print "People taller than height 10:",
    results = [client.decrypt(doc) for doc in s.find(index=client.get_ctL(10), iname = "height", relationship = -1)]
    results = parse(results)
    results = [dict(t) for t in set([tuple(d.items()) for d in results])]
    results.sort()
    print set([x["name"] for x in results]) == set([x["name"] for x in docs if x["height"] > 10])

    print "People smaller than height 10:",
    results = [client.decrypt(doc) for doc in s.find(index=client.get_ctL(10), iname = "height", relationship = 1)]
    results = parse(results)
    results = [dict(t) for t in set([tuple(d.items()) for d in results])]
    results.sort()
    print set([x["name"] for x in results]) == set([x["name"] for x in docs if x["height"] < 10])

    print "People smaller than height 10 with more than 30 years old:",
    results = [client.decrypt(doc) for doc in s.find_nested([["age", -1, client.get_ctL(30)], ["height", 1, client.get_ctL(10)]])]
    results = parse(results)
    results = [dict(t) for t in set([tuple(d.items()) for d in results])]
    results.sort()
    print set([x["name"] for x in results]) == set([x["name"] for x in docs if x["height"] < 10 and x["age"] > 30])

if __name__ == '__main__':
    main()
