#!/usr/bin/python
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
# This routine loads a dataset from a file named "synthetic_dataset.json" and generated
# by the script generate_dataset.py.
# 
# After that, a database named "benchmark" is created as well as two collections 
# named "encrypted" and "unencrypted". The dataset is inserted encrypted to the 
# former and unencrypted in the latter and speed results are printed.
# 

import json
from client import Client
from secmongo import SecMongo
from pymongo import MongoClient
from time import time
from index.indexnode import IndexNode
from index.avltree import AVLTree
import timeit


def load_stored_functions(db):
    # 
    # MongoDB's Stored functions
    # 
     
    db.system_js.sha256 = """function a(b){function c(a,b){return a>>>b|a<<32-b}for(var d,e,f=Math.pow,g=f(2,32),h="length",i="",j=[],k=8*b[h],l=a.h=a.h||[],m=a.k=a.k||[],n=m[h],o={},p=2;64>n;p++)if(!o[p]){for(d=0;313>d;d+=p)o[d]=p;l[n]=f(p,.5)*g|0,m[n++]=f(p,1/3)*g|0}for(b+="\\x80";b[h]%64-56;)b+="\\x00";for(d=0;d<b[h];d++){if(e=b.charCodeAt(d),e>>8)return;j[d>>2]|=e<<(3-d)%4*8}for(j[j[h]]=k/g|0,j[j[h]]=k,e=0;e<j[h];){var q=j.slice(e,e+=16),r=l;for(l=l.slice(0,8),d=0;64>d;d++){var s=q[d-15],t=q[d-2],u=l[0],v=l[4],w=l[7]+(c(v,6)^c(v,11)^c(v,25))+(v&l[5]^~v&l[6])+m[d]+(q[d]=16>d?q[d]:q[d-16]+(c(s,7)^c(s,18)^s>>>3)+q[d-7]+(c(t,17)^c(t,19)^t>>>10)|0),x=(c(u,2)^c(u,13)^c(u,22))+(u&l[1]^u&l[2]^l[1]&l[2]);l=[w+x|0].concat(l),l[4]=l[4]+w|0}for(d=0;8>d;d++)l[d]=l[d]+r[d]|0}for(d=0;8>d;d++)for(e=3;e+1;e--){var y=l[d]>>8*e&255;i+=(16>y?0:"")+y.toString(16)}return i};"""

    # Computes a mod b, where a is a hexadecimal string representation and b is 
    # a 16 bits word
    db.system_js.mod1_low = """function a(s, b){
            // Break "s" into 4-digit segments
            var a = s.match(/.{1,2}/g);
            var size = a.length;
            
            // Reverse each segment
            for(var i=0; i < size; i++)
                a[i] = parseInt(a[i].split("").reverse().join(""),16);
            
            a = a.reverse();

            var w = 0;// 32 bits
            var r; //16 bits
            for( var i = size - 1; i >= 0; i--){
                // a[i] is a 16 bits word
                w = (w << 16) | (a[i])
                r = parseInt(w/b)*(w >= b);
                w -= r*b*(w >= b);
            }

            return w;
        }"""

    db.system_js.orecompare ="""function a(ctL, ctR) {
            var kl = ctL[0];
            var h = ctL[1];
            var r = ctR[0];
            var v = ctR.splice(1);
            var H = mod1_low(sha256(kl + r),3);
            return (((v[h] - H) % 3) + 3) % 3; 
        }"""

    # 
    # Walk through the AVL tree looking for the target index
    # 

    db.system_js.walk =  """function a(ctL) {
       // Finds the root
    var node = db.customIndex.findOne({root:"1"});

    do{
        if ( node == null)
            return null;
        // Iterates through the tree
        cmp = orecompare(ctL, node.ctR);
        if(cmp == 1)
        // Greater than
        node = db.customIndex.findOne({_id:node.right});
        else if(cmp == 2)
        // Lower than
        node = db.customIndex.findOne({_id:node.left});

    } while ( node != null && cmp != 0);

        return node;
    }"""

#
datafile = open("synthetic_dataset.json")
dataset = json.load(datafile)

nMax = max(set([x["age"] for x in dataset]))
n = nMax+1
print "Maximum integer supported by the ORE cryptosystem: %d" % n
client = Client(Client.keygen(),n=n)

client.set_attr("email","static")
client.set_attr("firstname","static")
client.set_attr("surname","static")
client.set_attr("country","static")
client.set_attr("age","index")
client.set_attr("text","static")

s = SecMongo(add_cipher_param=pow(client.ciphers["h_add"].keys["pub"]["n"],2))
s.open_database("benchmark")
s.set_collection("encrypted")
s.drop_collection()
load_stored_functions(s.db)

print "%d items were loaded" % len(dataset)

#
client.encrypt(dataset[0])

dataset.sort(key=lambda x: x["age"])

def build_index(dataset):
    root = AVLTree([dataset[0]["age"],0],nodeclass=IndexNode)
    for i,doc in enumerate(dataset[1:]):
        root = root.insert([doc["age"],i+1])

    # assert it is correct
    for data in dataset:
        assert root.find(data["age"])
    return root

def load_encrypted_data():
    # Build a index
    index = build_index(dataset)
    index.encrypt(client.ciphers["index"])
    encrypted_dataset = []
    for data in dataset:
        encrypted_dataset.append(client.encrypt(data))

    s.insert_indexed(index,encrypted_dataset)

diff = timeit.timeit("load_encrypted_data()",setup="from __main__ import load_encrypted_data",number=1)
print "Encrypted data loaded in %fs - %f elements/s" % (diff,len(dataset)/(diff))

s.collection.create_index([("index",SecMongo.ASCENDING)])

def encrypted_query():
	return s.find(index=client.get_ctL(nMax))

# print "Looking for " + str(client.get_ctL(nMax))
diff = timeit.timeit("encrypted_query()",setup="from __main__ import encrypted_query",number=100)
print "Encrypted query in %fs" % (diff)

def load_data():
	count = 0
	start = time()
	for entry in dataset:
		if (count % 1000) == 0:
			# 
			# print "%d - %f elements/s" % (count, 1000/(time()-start))
			start = time()
		count = count + 1
		collection.insert(entry)

unencrypted_client = MongoClient()
db = unencrypted_client["benchmark"]
collection = db["unencrypted"]
collection.drop()

diff = timeit.timeit("load_data()",setup="from __main__ import load_data",number=1)
print "Unencrypted data loaded in %fs - %f elements/s" % (diff,len(dataset)/(diff))

# Create index
collection.create_index([("age", SecMongo.ASCENDING)])

def query_range(predicate,projection):
	result = []
	for x in s.find(sort=[("age",SecMongo.DESCENDING)],projection=projection):
		result.append(x)
	return result

def unencrypted_query():
	return collection.find_one({"age":nMax})
diff = timeit.timeit("unencrypted_query()",setup="from __main__ import unencrypted_query",number=100)
print "Unencrypted query in %fs" % (diff)
