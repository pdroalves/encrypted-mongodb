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

load_stored_functions(s.db)


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
