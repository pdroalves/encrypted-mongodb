#!/usr/bin/python
# coding: utf-8
# 
##########################################################################
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
#
# This routine generates a dataset; instantiates and sets the Client class. 
# After that the dataset is inserted in a local mongo database and some 
# queries are executed.
# 
from client import Client
from secmongo import SecMongo
from bson.json_util import dumps
from index.avltree import AVLTree
from index.indexnode import IndexNode

#
# Input data
#
docs = [
	{
		"name":"John Snow",
		"age": 18,
		"address":"Castle Black, over a table",

	},
	{
		"name":"Eddard Stark",
		"age": 40,
		"address":"King's landing, in a spear",
	},
	{
		"name":"Catherine Stark",
		"age": 34,
		"address":"Hell, 123",
	},
	{
		"name":"Rob Stark",
		"age": 20,
		"address":"Hell, 124",
	},
	{
		"name":"Aria Stark",
		"age": 12,
		"address":"Braavos",
	},
	{
		"name":"Sansa Stark",
		"age": 16,
		"address":"North",
	},
	{
		"name":"Theon Greyjoy",
		"age": 19,
		"address":"No Dick's land",
	},
	{
		"name":"Tywin Lannister",
		"age": 55,
		"address":"King's landing",
	},
	{
		"name":"Cersei Lannister",
		"age": 35,
		"address":"King's landing",
	},
	{
		"name":"Jaime Lannister",
		"age": 35,
		"address":"King's landing",
	},
	{
		"name":"Robert Baratheon",
		"age": 41,
		"address":"King's landing",
	},
	{
		"name":"Joffrey Baratheon",
		"age": 17,
		"address":"King's landing",
	},
	{
		"name":"Lady Melissandre",
		"age": 201,
		"address":"Castle Black, naked",
	}
]
#
##
#
# Minha construção da árvore AVL está bugada.
# Preciso passar as entradas em ordenação crescente para
# garantir a correção
docs.sort(key=lambda x: x["age"])

# Setup client
client = Client(Client.keygen(),n=202)

client.set_attr("address","static")
client.set_attr("name","static")
client.set_attr("age","index")

# Setup the MongoDB driver
s = SecMongo(add_cipher_param=pow(client.ciphers["h_add"].keys["pub"]["n"],2))
s.open_database("test_ore")
s.set_collection("gameofthrones")
s.drop_collection()

def build_index():
	root = AVLTree([docs[0]["age"],0],nodeclass=IndexNode)
	for i,doc in enumerate(docs[1:]):
		root = root.insert([doc["age"],i+1])

	# assert it is correct
	for doc in docs:
		assert root.find(doc["age"])
	return root

# Build a index
index = build_index()

# Encrypt
index.encrypt(client.ciphers["index"])
encrypted_docs = []
for doc in docs:
	encrypted_docs.append(client.encrypt(doc))

s.insert_indexed(index,encrypted_docs)
print "Database:"
result = [client.decrypt(x)["name"] for x in s.find()]
assert result == [x["name"] for x in docs]
print result

print ""
print "Someone with 17 years old:"
for doc in s.find(index=client.get_ctL(17),projection=["name","age","level"]):
	print client.decrypt(doc)

print ""
print "Someone with 201 years old:"
for doc in s.find(index=client.get_ctL(201),projection=["name","age","level"]):
	print client.decrypt(doc)

see = lambda x: "%s => %s %s" % (x.me.value, x.left.me.value if x.left else None, x.right.me.value if x.right else None)
