#!/usr/bin/python
# coding: utf-8

from client import Client
from secmongo import SecMongo
from bson.json_util import dumps

docs = [
	{
		"name":"John Snow",
		"age": 18,
		"level":0,
		"address":"Castle Black, over a table",
		"keywords":["Snow","Castle Black","Dead"]

	},
	{
		"name":"Eddard Stark",
		"age": 40,
		"level":0,
		"address":"King's landing, in a spear",
		"tags":["Stark","Dead"]
	},
	{
		"name":"Catherine Stark",
		"age": 35,
		"level":0,
		"address":"Hell, 123",
		"tags":["Stark","Dead"]
	},
	{
		"name":"Rob Stark",
		"age": 20,
		"level":0,
		"address":"Hell, 124","tags":["Stark","Dead"]
	},
	{
		"name":"Aria Stark",
		"age": 12,
		"level":0,
		"address":"Braavos",
		"tags":["Stark"]
	},
	{
		"name":"Sansa Stark",
		"age": 16,
		"level":0,
		"address":"North",
		"tags":["Stark"]
	},
	{
		"name":"Theon Greyjoy",
		"age": 19,
		"level":0,
		"address":"No Dick's land",
		"tags":"Greyjoy"
	},
	{
		"name":"Tywin Lannister",
		"age": 55,
		"level":0,
		"address":"King's landing",
		"tags":["Lannister","Dead"]
	},
	{
		"name":"Cersei Lannister",
		"age": 35,
		"level":0,
		"address":"King's landing",
		"tags":"Lannister"
	},
	{
		"name":"Jaime Lannister",
		"age": 35,
		"level":0,
		"address":"King's landing",
		"tags":"Lannister"
	},
	{
		"name":"Robert Baratheon",
		"age": 41,
		"level":0,
		"address":"King's landing",
		"tags":["Baratheon","King","Dead"]
	},
	{
		"name":"Joffrey Baratheon",
		"age": 17,
		"level":0,
		"address":"King's landing",
		"tags":["Lannister","Baratheon","King"]
	},
	{
		"name":"Lady Melisandre",
		"age": 432,
		"level":0,
		"address":"Castle Black, naked",
		"tags":["Melisandre","Witch","Hot","Ugly"]
	}
]

client = Client(Client.keygen())

client.set_attr("address","static")
client.set_attr("name","static")
client.set_attr("tags","keyword")
client.set_attr("age","range")
client.set_attr("level","h_add")

s = SecMongo(add_cipher_param=pow(client.ciphers["h_add"].keys["pub"]["n"],2))
s.open_database("test")
s.set_collection("gameofthrones")
s.drop_collection()

for doc in docs:
	ct = client.encrypt(doc)
	s.insert(ct)



print "Database:"
print [client.decrypt(x)["name"] for x in s.find()]
print ""
print "Starks:"
for x in s.find(client.get_ibe_sk(["Stark"]),projection=["name","age"]):
	print dumps( client.decrypt( x ),indent = 4 )

print ""
print "Lannisters:"
for x in s.find(client.get_ibe_sk(["Lannister"]),projection=["name","age"]):
	print dumps( client.decrypt( x ),indent = 4 )

print ""
print "Lannisters and Baratheons:"
baratheon = client.get_ibe_sk(["Baratheon"])
lannister = client.get_ibe_sk(["Lannister"])
for x in s.find([baratheon,lannister],projection=["name","age"]):
	print dumps( client.decrypt( x ),indent = 4 )

# print ""
print "The oldest person:"
elder = s.find(sort=[("age",SecMongo.DESCENDING)],projection=["name","age","level"]).next()
print dumps( client.decrypt(elder), indent=4 )

# Will update melissandre age
diff = client.encrypt({"$inc":{"level":20}},kind="update")
s.update(client.get_ibe_sk(["Witch"]),diff)

print ""
print "The oldest person:"
elder = s.find(sort=[("age",SecMongo.DESCENDING)],projection=["name","age","level"]).next()
print dumps( client.decrypt(elder), indent=4 )
