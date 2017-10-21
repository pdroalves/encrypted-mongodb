#!/usr/bin/python
# coding:  utf-8
##########################################################################
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
##########################################################################
#
# Queries used for the encrypted netflix dataset
# This script must be run using ipython
#
from pymongo import MongoClient
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
import tqdm
import calendar
from datetime import datetime
import tempfile
from bson.objectid import ObjectId
import operator
from bson import json_util
from IPython import get_ipython
ipython = get_ipython()

def egcd(a, b):
    if a == 0:
        return (b, 0, 1)
    else:
        g, y, x = egcd(b % a, a)
        return (g, x - (b // a) * y, y)

def modinv(a, m):
    g, x, y = egcd(a, m)
    if g != 1:
        raise Exception('modular inverse does not exist')
    else:
        return x % m
##############################
# Setup client
start = time.time()
client = Client(Client.keygen())
client.ciphers["h_add"].rating_cts = [client.ciphers["h_add"].encrypt(m) for m in range(6)]
print client.keys
# Attributes should be classified using add_attr(). This action will imply in
# ciphertexts stored with all tagged attributes. There is no relation with
# the indexing itself.
client.add_attr(attribute = "static", name = "movieid")
client.add_attr(attribute = "static", name = "customerid")
client.add_attr(attribute = "static", name = "rating")
client.add_attr(attribute = "static", name = "date")
client.add_attr(attribute = "index", name = "date")
client.add_attr(attribute = "index", name = "rating")
client.add_attr(attribute = "h_add", name = "rating")
# inames will be used to build the indexing
inames = ["customerid", "movieid", "date"]

##############################
# Setup the MongoDB driver
s = SecMongo(url="gtxtitan", add_cipher_param=pow(client.ciphers["h_add"].keys["pub"]["n"], 2))
s.open_database("netflix")
s.set_collection("data")

##############################
# Queries
from random import randint 

def parse(doc):
    parsed_doc = {}
    keys = doc.keys()
    for key in keys:
        if key == "_id":
            parsed_doc[key] = doc[key]
        elif "static" in doc[key]:
            parsed_doc[key] = doc[key]["static"]
    return parsed_doc

# 
# Select a random movie and a random customer from the database
#
MID = 6287
AID = 1061110
BID = 2486445
start_date = 1041379200
end_date = 1072915200 # 1 year
start_date_ctL = client.get_ctL(start_date)
end_date_ctL = client.get_ctL(end_date) # 1 year
MID_ctL = client.get_ctL(MID)
AID_ctL = client.get_ctL(AID)
BID_ctL = client.get_ctL(BID)

rate_hated = client.get_ctL(2)
rate_loved = client.get_ctL(4)

# Print
print "AID: %d, MID: %d" % (AID, MID)

# 
# Equation 2: Movies rated by Alice
# 
print "Equation 2:"
ipython.magic("timeit list(s.find( index = AID_ctL, iname = 'customerid', projection = ['movieid', 'customerid'] ))")
# 
# Equation 4: Users that rated M
# 
print "Equation 4:"
ipython.magic("timeit list(s.find( index = MID_ctL, iname = 'movieid', projection = ['movieid', 'customerid']))")
# 
# Equation 5: Average of Alice's ratings over time
# 
# Return a list of ratings that happened in a specific time interval
# 


print "T:[%d, %d]" % (start_date, end_date)
print "Equation 5:"
ipython.magic("timeit  list(s.find_nested([ ['customerid', 0, AID_ctL], ['date', 42, [start_date_ctL, end_date_ctL]]], return_ids = True))")

# 
# Equation 6: Average of ratings for a particular movie M in a timeset
# 
# Return the sum of all ratings in a a list that happened in a specific time
# interval and the number of ratings.
# 
print "Equation 6:"
n2 = pow(client.ciphers["h_add"].keys["pub"]["n"],2)
outcome = list(s.find_nested([['movieid', 0, MID_ctL],['date', 42, [start_date_ctL, end_date_ctL]]]))
ipython.magic("timeit list(s.find_nested([['movieid', 0, MID_ctL],['date', 42, [start_date_ctL, end_date_ctL]]], return_ids = True))")
ratings = [int(x["rating"]["h_add"]) for x in outcome]
ipython.magic("timeit reduce(lambda x,y: x*y % n2, ratings)")

#
# Equation 7: Number of days since Alice's first rating
#
# Get Alice ratings, sort and get the oldest. Compute: t - oldest mod n2
#
print "Equation 7:"
ipython.magic("timeit list(s.find( index = AID_ctL, iname = 'customerid', projection = ['date', 'customerid']))")
outcome = list(s.find( index = AID_ctL, iname = "customerid", projection = ["date", "customerid"]))
ipython.magic("timeit outcome.sort(cmp = lambda x, y: client.ciphers['index'].compare(x['date']['index'][0],y['date']['index'][1]))")

#
# Equation 8: Quantity of users who hated M
#
# Get all users that rated M and compare to rate_hated
#
print "Equation 8:"
outcome = s.find( index = MID_ctL, iname = "movieid", projection = ["rating"] )
ipython.magic("timeit s.find( index = MID_ctL, iname = 'movieid', projection = ['rating'] )")
ore_compare = lambda x, y: client.ciphers["index"].compare(x,y)

hold = [client.get_ctR(parse(client.decrypt(x))["rating"]) for x in outcome]
count = sum([1 if (ore_compare(rate_hated, enc_rate) == 1) else 0 for enc_rate in hold])
ipython.magic("timeit sum([1 if (ore_compare(rate_hated, enc_rate) == 1) else 0 for enc_rate in hold])")
# ipython.magic("timeit sum([1 if (ore_compare(rate_hated, enc_rate["rating"]["index"]) == 1) else 0 for enc_rate in outcome])")


#
# Equation 9: Quantity of users who loved M
#
# Get all users that rated M and compare to rate_loved
#
print "Equation 9:"
ipython.magic("timeit s.find( index = MID_ctL, iname = 'movieid', projection = ['rating'] )")
ipython.magic("timeit sum([1 if (ore_compare(client.get_ctL(rate_loved), enc_rate['rating']['index']) == -1) else 0 for enc_rate in outcome])")

#
# Equation 11: Users similar to Alice
#
print "Equation 11:"
def similarity_set(A, B):
	C = []

	for x in B:
		for y in A:
			if ore_compare(x["movieid"]["index"][0], y["movieid"]["index"][1]) == 0:
				C.append([x["rating"]["h_add"], y["rating"]["h_add"]])
	return C
A = s.find(
	index = AID_ctL,
	iname = "customerid",
	projection = ["movieid","rating"]
	)

B = s.find(
	index = BID_ctL,
	iname = "customerid",
	projection = ["movieid", "rating"]
	)
ipython.magic("timeit s.find( index = AID_ctL, iname = 'customerid', projection = ['movieid','rating'], return_ids = True )")
ipython.magic("timeit s.find( index = BID_ctL, iname = 'customerid', projection = ['movieid','rating'], return_ids = True )")

S = similarity_set(A, B)
ipython.magic("timeit similarity_set(A, B)")
def egcd(a, b):
    if a == 0:
        return (b, 0, 1)
    else:
        g, y, x = egcd(b % a, a)
        return (g, x - (b // a) * y, y)

def modinv(a, m):
    g, x, y = egcd(a, m)
    if g != 1:
        raise Exception('modular inverse does not exist')
    else:
        return x % m
ipython.magic("timeit reduce(lambda x,y: x*y % n2, [x*modinv(y,n2) % n2 for (x,y) in S])")