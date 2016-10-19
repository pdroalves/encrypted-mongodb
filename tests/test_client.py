#!/usr/bin/env python
# coding: utf-8

from client import Client

docs = [
	{
		"name":"John Snow",
		"age": 18,
		"address":"Castle Black, over a table",
		"keywords":["Snow","Castle Black","Dead"]

	},
	{
		"name":"Eddard Stark",
		"age": 40,
		"address":"King's landing, in a spear",
		"tags":["Stark","Dead"]
	},
	{
		"name":"Catherine Stark",
		"age": 35,
		"address":"Hell, 123",
		"tags":["Stark","Dead"]
	},
	{
		"name":"Rob Stark",
		"age": 20,
		"address":"Hell, 124","tags":["Stark","Dead"]
	},
	{
		"name":"Aria Stark",
		"age": 12,
		"address":"Braavos",
		"tags":["Stark"]
	},
	{
		"name":"Sansa Stark",
		"age": 16,
		"address":"North",
		"tags":["Stark"]
	},
	{
		"name":"Theon Greyjoy",
		"age": 19,
		"address":"No Dick's land",
		"tags":"Greyjoy"
	},
	{
		"name":"Tywin Lannister",
		"age": 55,
		"address":"King's landing",
		"tags":["Lannister","Dead"]
	},
	{
		"name":"Cersei Lannister",
		"age": 35,
		"address":"King's landing",
		"tags":"Lannister"
	},
	{
		"name":"Jaime Lannister",
		"age": 35,
		"address":"King's landing",
		"tags":"Lannister"
	},
	{
		"name":"Robert Baratheon",
		"age": 41,
		"address":"King's landing",
		"tags":["Baratheon","King","Dead"]
	},
	{
		"name":"Joffrey Baratheon",
		"age": 17,
		"address":"King's landing",
		"tags":["Lannister","Baratheon","King"]
	},
	{
		"name":"Lady Melissandre",
		"age": 432,
		"address":"Castle Black, naked",
		"tags":["Witch","Hot","Ugly"]
	}
]

print "Instantiating the client"

client = Client(Client.keygen())

client.set_attr("address","static")
client.set_attr("name","static")
client.set_attr("tags","keyword")
client.set_attr("age","static")

print "Query encryption"

print "Encrypt docs[0]"
print docs[0]
print client.encrypt(docs[0])
print ""
print "Encrypt search query"
print client.encrypt({"tags":"Hot"},"search")
print ""
for doc in docs:
	print "Decrypted: %s" % client.decrypt(client.encrypt(doc))
