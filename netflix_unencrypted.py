#!/usr/bin/python
# coding: utf-8
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
# Queries used for the non-encrypted netflix dataset
# This script must be run using ipython
# 
import pymongo
from pymongo import MongoClient
from IPython import get_ipython
ipython = get_ipython()

client = MongoClient("gtxtitan")
netflix = client.get_database("unencrypted_netflix").data

aid = 1061110
bid = 2486445
mid = 6287
start_date = 1041379200
end_date = 1072915200
rate_hated = 2
rate_loved = 4

print "Equation 2"
ipython.magic("timeit list(netflix.find({'customerid':aid}, projection = {'movieid':1}))")

print "Equation 4"
ipython.magic("timeit list(netflix.find({'movieid':mid}, projection = {'customerid':1}))")

print "Equation 5"
ipython.magic("timeit sum([int(x['rating']) for x in netflix.find({'customerid':aid, 'date':{'$gt':start_date}, 'date':{'$lt':end_date}})])")

print "Equation 6"
ipython.magic("timeit sum([int(x['rating']) for x in netflix.find({'$and':[{'movieid':mid}, {'date':{'$gt':start_date}}, {'date':{'$lt':end_date}}]})])")

print "Equation 7"
ipython.magic("timeit first = end_date - netflix.find({'customerid':aid}, projection = {'date':1}).sort('date',pymongo.ASCENDING).next()['date']")

print "Equation 8"
ipython.magic("timeit list(netflix.find({'$and':[{'movieid':mid}, {'rating':{'$lt':rate_hated}}]}))")

print "Equation 9"
ipython.magic("timeit list(netflix.find({'$and':[{'movieid':mid}, {'rating':{'$gt':rate_loved}}]}))")

print "Equation 11"
def similarity_set(A, B):
	C = set([x['movieid'] for x in A]).intersection(set([x['movieid'] for x in B]))
	result = []
	print len(C)
	for x in C:
		z = dict()
		z['movieid'] = x
		z["RatingA"] = (doc for doc in A if doc['movieid'] == x).next()['rating']
		z["RatingB"] = (doc for doc in B if doc['movieid'] == x).next()['rating']
		result.append(z)
	return result

A = list(netflix.find({'customerid':aid}, projection = {'movieid':1, 'rating':1}))
B = list(netflix.find({'customerid':bid}, projection = {'movieid':1, 'rating':1}))
S = similarity_set(A, B)
ipython.magic("timeit A = list(netflix.find({'customerid':aid}, projection = {'movieid':1, 'rating':1}))")
ipython.magic("timeit B = list(netflix.find({'customerid':bid}, projection = {'movieid':1, 'rating':1}))")
ipython.magic("timeit S = similarity_set(A, B)")
ipython.magic("timeit sum([abs(x['RatingA'] - x['RatingB']) for x in S])/len(S)")