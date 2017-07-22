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


# def main():
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
client.set_attr("name", "static")
client.set_attr("address", "static")
client.set_attr("age", "index")
client.set_attr("height", "index")

# Setup the MongoDB driver
s = SecMongo(add_cipher_param=pow(client.ciphers["h_add"].keys["pub"]["n"],
                                  2),
             url='mongodb://localhost:27017')
s.open_database("test_sec")
s.set_collection("gameofthrones")
s.drop_collection()

print("Starting now.")
start = time.time()
for i, doc in enumerate(docs):
    enc_doc = client.encrypt(doc)
    index = s.insert(enc_doc)
    node = EncryptedNode(client.ciphers["index"].encrypt(doc["age"]), index)
    s.insert_index(node, "age")
    node = EncryptedNode(client.ciphers["index"].encrypt(doc["height"]), index)
    s.insert_index(node, "height")

# print("Insert time: ", time.time() - start)
# result = [client.decrypt(x)["name"] for x in s.find()]
# print("")

print("People of 35 years old:")
for doc in s.find(index=client.get_ctL(35), iname = "age", relationship = 0):
    print(client.decrypt(doc))

print("People older than 35 years old:")
for doc in s.find(index=client.get_ctL(35), iname = "age", relationship = 1):
    print(client.decrypt(doc))

print("People younger than 35 years old:")
for doc in s.find(index=client.get_ctL(35), iname = "age", relationship = -1):
    print(client.decrypt(doc))

print("People of height 10:")
for doc in s.find(index=client.get_ctL(10), iname = "height", relationship = 0):
    print(client.decrypt(doc))

print("People taller than height 10:")
for doc in s.find(index=client.get_ctL(10), iname = "height", relationship = 1):
    print(client.decrypt(doc))

print("People smaller than height 10:")
for doc in s.find(index=client.get_ctL(10), iname = "height", relationship = -1):
    print(client.decrypt(doc))



# if __name__ == '__main__':
#     main()
