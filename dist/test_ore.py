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


def main():
    #
    # Input data
    #
    docs = [
        {
            "name": "John Snow",
            "age":  18,
            "address": "Castle Black, over a table",

        },
        {
            "name": "Eddard Stark",
            "age":  40,
            "address": "King's landing, in a spear",
        },
        {
            "name": "Catherine Stark",
            "age":  34,
            "address": "Hell, 123",
        },
        {
            "name": "Rob Stark",
            "age":  20,
            "address": "Hell, 124",
        },
        {
            "name": "Aria Stark",
            "age":  12,
            "address": "Braavos",
        },
        {
            "name": "Sansa Stark",
            "age":  16,
            "address": "North",
        },
        {
            "name": "Theon Greyjoy",
            "age":  19,
            "address": "No Dick's land",
        },
        {
            "name": "Tywin Lannister",
            "age":  55,
            "address": "King's landing",
        },
        {
            "name": "Cersei Lannister",
            "age":  35,
            "address": "King's landing",
        },
        {
            "name": "Jaime Lannister",
            "age":  35,
            "address": "King's landing",
        },
        {
            "name": "Robert Baratheon",
            "age":  41,
            "address": "King's landing",
        },
        {
            "name": "Joffrey Baratheon",
            "age":  17,
            "address": "King's landing",
        },
        {
            "name": "Lady Melissandre",
            "age":  201,
            "address": "Castle Black, naked",
        }
    ]
    # Setup client
    client = Client(Client.keygen())
    client.set_attr("title", "static")
    client.set_attr("year", "index")

    # Setup the MongoDB driver
    s = SecMongo(add_cipher_param=pow(client.ciphers["h_add"].keys["pub"]["n"], 2),
                 url='mongodb://localhost:27017')
    s.open_database("test_sec")
    s.set_collection("gameofthrones2")
    s.drop_collection()

    s.load_scripts()
    docs = []
    with open("movies.list") as movies_file:
        for line in movies_file:
            movie = re.search("(.*?)\t+(\d{4})", line)
            if(movie):
                docs.append({'title': movie.group(1), 'year': int(movie.group(2))})

    root = None
    print("Starting now.")
    start = time.time()
    for i, doc in enumerate(docs[:5000]):
        print(i)
        enc_doc = client.encrypt(doc)
        inserted_doc = s.insert(enc_doc)
        node = EncryptedNode(client.ciphers["index"].encrypt(doc["year"]),
                             inserted_doc)
        s.insert_index(node)

    print("insert time: ", time.time() - start)
    result = [client.decrypt(x)["title"] for x in s.find()]
    print("")
    print("Movie from 2015:")
    for doc in s.find(index=client.get_ctL(2015)):
        print(client.decrypt(doc))
        # pass

if __name__ == '__main__':
    main()
