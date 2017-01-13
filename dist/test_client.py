#!/usr/bin/env python
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
# This routine generates a dataset; instantiates and sets the Client class; and 
# test encrypt/decrypt functions.  
# 

from client import Client

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
        "age": 35,
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

client = Client(Client.keygen(),n=202)
print "Instantiating the client"

client.set_attr("address","static")
client.set_attr("name","static")
client.set_attr("age","index")

print "Query encryption"

print "Encrypt docs[0]"
print docs[0]
print client.encrypt(docs[0])
print ""
print "Encrypt search query"
print client.get_ctL(41)
print ""
for doc in docs:
    print "Decrypted: %s" % client.decrypt(client.encrypt(doc))
