#!/usr/bin/python
# coding: utf-8
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
import pymongo
from pymongo import MongoClient
from .crypto import paillier
from .crypto import elgamal
from .crypto.ore import ORE
from .index.avltree import AVLTree
from .index.indexnode import IndexNode
from bson.json_util import dumps
import json
import os


class StopLookingForThings(Exception):
    pass


class SecMongo:
    ASCENDING = pymongo.ASCENDING
    DESCENDING = pymongo.DESCENDING

    client = None
    db = None
    collection = None

    __ciphers = {"index": None, "h_add": None, "h_mul": None}

    def __init__(self, add_cipher_param=None, url=None):
        assert url is None or type(url) == str

        # Connects to database
        if url:
            self.client = MongoClient(url)
        else:
            self.client = MongoClient()

        self.__ciphers["index"] = ORE
        self.__ciphers["h_add"] = paillier.Paillier()
        self.__ciphers["h_add"].add_to_public_key("n2", add_cipher_param)
        self.__ciphers["h_mul"] = elgamal.ElGamal()

    def open_database(self, database):
        assert type(database) is str
        self.db = self.client[database]

    def derp(self):
        self.db.system_js.rebalance_avl(self.index_collection.name, 1)

    def load_scripts(self):
        assert self.db
        script_dir = os.path.join(os.path.dirname(__file__), 'scripts')
        scripts = filter(lambda x: x.endswith('.js'), os.listdir(script_dir))
        for script in scripts:
            with open(os.path.join(script_dir, script), 'r') as js_file:
                setattr(self.db.system_js, script.strip('.js'),
                        ''.join(js_file.readlines()))

    def set_collection(self, collection):
        assert type(collection) is str
        self.collection = self.db[collection]
        self.index_collection = self.db["indexes-"+collection]

    def find(self, index=None, relationship = 0, projection=None, iname=None):
        if index is None:
            return self.collection.find()

        # Search by an index
        # This method expects an index value (the ctL)
        ctL = index  # a

        #  To search for elements with an attribute named "age" with a value
        #  between 30 and 40
        #
        #  The query MUST be encrypted

        # Get the tree root
        node = self.index_collection.find_one({"parent": None, "iname":iname})
        while node is not None:
            ctR = node["ctR"]  # b
            r = self.__ciphers["index"].compare(ctL, ctR)

            if relationship == 0: # Equality
                if r == 0:
                    # Found
                    # a == b
                    return self.collection.find({"_id": {"$in": node["index"]}})
                elif r == 1:
                    # a > b
                    node = self.index_collection.find_one(
                        {"_id": node["right"]}
                    )
                else:
                    # a < b
                    node = self.index_collection.find_one(
                        {"_id": node["left"]}
                    )
                    assert r == -1
            elif relationship == 1: # > than
                if r == 0:
                    # Found
                    # a == b
                    return self.__get_branch(self.index_collection.find_one(
                                                {"_id": node["right"]}
                                            ))
                elif r == 1:
                    # a < b
                    node = self.index_collection.find_one(
                        {"_id": node["right"]}
                    )
                else:
                    assert r == -1
                    # Found
                    # a > b
                    return self.__get_branch(self.index_collection.find_one(
                                                {"_id": node["right"]}
                                            ))
            else: # < than
                assert relationship == -1
                if r == 0:
                    # Found
                    # a == b
                    return self.__get_branch(self.index_collection.find_one(
                                                {"_id": node["left"]}
                                            ))
                elif r == 1:
                    # a > b
                    # Found
                    return self.__get_branch(self.index_collection.find_one(
                        {"_id": node["left"]}
                    ))
                else:
                    assert r == -1
                    # a < b
                    node = self.index_collection.find_one(
                        {"_id": node["left"]}
                    )

        return None

    # selection: a query in the same format required by find()
    # diff: A single dict in the format:
    #     {operation:{field1:Enc(value1),field2:Enc((value2),...}}
    def update(self, selection, diff):
        # Select and update a set of entries
        operation = diff.keys()[0]
        output = []
        s = self.find(selection, projection=["_id"] + diff[operation].keys())

        if operation in ["$inc", "$dec"]:
            field_kind = "h_add"

            cipher = self.__ciphers[field_kind]
            for document in s:
                for attribute in diff[operation]:
                    A = diff[operation][attribute]
                    B = document[attribute]

                    result = cipher.h_operation(A, B)

                    output.append(self.collection.update(
                        {"_id": document["_id"]},
                        {"$set": {attribute: result}})
                    )
        elif operation == "$set":
            output = [self.collection.update({"_id": x["_id"]},
                                             diff) for x in s]
        else:
            raise ValueError()

        return output

    def insert(self, doc):
        return self.collection.insert(doc)

    def print_index(self, node=None, spaces=0):
        if(not node):
            node = self.index_collection.find_one({"root": "1"})
            print("Root Index: ", node['index'])
        if(node['right']):
            print(' ' * spaces, 'right', self.print_index(self.index_collection.find_one({"_id": node["right"]}), spaces=spaces+4))
        if(node['left']):
            print(' ' * spaces, 'left', self.print_index(self.index_collection.find_one({"_id": node["left"]}), spaces=spaces+4))
        return node['index']

    #
    # iname: Index collection name
    #
    def insert_index(self, index, iname = None):
        ctL = index.value[0]
        node = self.index_collection.find_one({"parent": None, "iname": iname})
        if not node:
            self.index_collection.insert_one({
                "index": [index._id],
                "ctR": index.value[1],
                "parent": None,
                "left": None,
                "right": None,
                "iname": iname, 
                "height": 1
            })
            return

        while node is not None:
            ctR = node["ctR"]
            r = self.__ciphers["index"].compare(ctL, ctR)
            if r == 0:
                # The node already exists in the tree
                self.index_collection.update(
                    {"_id": node['_id']},
                    {"$addToSet": {"index": index._id}}
                )
                return
            elif r == 1:
                # index is higher than this node.
                if node["right"] is None:
                    # This was a leaf.
                    # Add right index
                    new = self.index_collection.insert_one({
                        "index": [index._id],
                        "ctR": index.value[1],
                        "parent": node['_id'],
                        "left": None,
                        "right": None,
                        "iname": iname, 
                        "height": 1
                    })
                    self.index_collection.update(
                        {"_id": node['_id']},
                        {"$set": {"right": new.inserted_id}}
                    )
                    break
                else:
                    node = self.index_collection.find_one(
                        {"_id": node["right"], "iname": iname}
                    )
            elif r == -1:
                # index is lower than this node.
                if node["left"] is None:
                    # This was a leaf.
                    # Add left index
                    new = self.index_collection.insert_one({
                        "index": [index._id],
                        "ctR": index.value[1],
                        "parent": node['_id'],
                        "left": None,
                        "right": None,
                        "iname": iname, 
                        "height": 1
                    })
                    self.index_collection.update(
                        {"_id": node['_id']},
                        {"$set": {"left": new.inserted_id}}
                    )
                    break
                else:
                    node = self.index_collection.find_one(
                        {"_id": node["left"], "iname": iname}
                    )
        self.db.system_js.update_height(self.index_collection.name,
                                        new.inserted_id,
                                        iname)
        self.db.system_js.rebalance_avl(self.index_collection.name,
                                        new.inserted_id,
                                        iname)

        # self.balance_node(self.index_collection.find_one({"parent": None}))

    def balance_node(self, node):
        if node:
            left = self.index_collection.find_one({"_id": node["left"]})
            left_balance, left_height = self.balance_node(left)

            right = self.index_collection.find_one({"_id": node["right"]})
            right_balance, right_height = self.balance_node(right)

            node = self.index_collection.find_one(
                {"_id": node["_id"]}
            )
            left = self.index_collection.find_one({"_id": node["left"]})
            right = self.index_collection.find_one({"_id": node["right"]})

            self_balance = (right_height - left_height)
            if self_balance not in [-1, 0, 1]:
                print("unbalance")
                if self_balance > 0:
                    parent = self.index_collection.find_one(
                        {"_id": right["_id"]}
                    )
                    if right_balance < 0:
                        self.right_rotate(right)
                        node = self.index_collection.find_one(
                            {"_id": node["_id"]}
                        )
                        parent = self.index_collection.find_one(
                            {"_id": right["left"]}
                        )
                    self.left_rotate(node)
                elif self_balance < 0:
                    parent = self.index_collection.find_one(
                        {"_id": left["_id"]}
                    )
                    if left_balance > 0:
                        self.left_rotate(left)
                        node = self.index_collection.find_one(
                            {"_id": node["_id"]}
                        )
                        parent = self.index_collection.find_one(
                            {"_id": left["right"]}
                        )
                    self.right_rotate(node)
                return self.balance_node(parent)

            return self_balance, max(left_height, right_height) + 1
        else:
            return 0, 0

    def right_rotate(self, node):
        left = self.index_collection.find_one({"_id": node["left"]})
        # Set original left child's right child parent to node.
        if(left['right']):
            self.index_collection.update(
                {"_id": left['right']},
                {"$set": {"parent": node['_id']}}
            )
        # Set original parent child to left child of node.
        if(node["parent"]):
            parent = self.index_collection.find_one({"_id": node["parent"]})
            side = 'left' if parent['left'] == node['_id'] else 'right'
            if side == 'left':
                self.index_collection.update(
                    {"_id": parent['_id']},
                    {"$set": {"left": left['_id']}}
                )
            elif side == 'right':
                self.index_collection.update(
                    {"_id": parent['_id']},
                    {"$set": {"right": left['_id']}}
                )
        # Set orginal left's parent to node's original parent.
        self.index_collection.update(
            {"_id": left['_id']},
            {"$set": {"parent": node['parent'], "right": node['_id']}}
        )
        # Set node's left child to left's original right child update parent of
        # node to original left child.
        self.index_collection.update(
            {"_id": node['_id']},
            {"$set": {"left": left['right'], "parent": left['_id']}}
        )

    def left_rotate(self, node):
        right = self.index_collection.find_one({"_id": node["right"]})
        # Set original left child's right child parent to node.
        if(right['left']):
            self.index_collection.update(
                {"_id": right['left']},
                {"$set": {"parent": node['_id']}}
            )
        # Set original parent child to right child of node.
        if(node["parent"]):
            parent = self.index_collection.find_one({"_id": node["parent"]})
            side = 'left' if parent['left'] == node['_id'] else 'right'
            if side == 'left':
                self.index_collection.update(
                    {"_id": parent['_id']},
                    {"$set": {"left": right['_id']}}
                )
            elif side == 'right':
                self.index_collection.update(
                    {"_id": parent['_id']},
                    {"$set": {"right": right['_id']}}
                )

        # Set orginal right's parent to node's original parent.
        self.index_collection.update(
            {"_id": right['_id']},
            {"$set": {"parent": node['parent'], "left": node['_id']}}
        )
        # Set node's right child to right's original right child update parent
        # of node to original right child.
        self.index_collection.update(
            {"_id": node['_id']},
            {"$set": {"right": right['left'], "parent": right['_id']}}
        )

    def insert_tree(self, node):
        if node is None:
            return None
        # Down the tree from its root, build a index-document and add to the
        # database.
        new_doc = {"index": node.me._id,  # pointer to data
                   "ctR": node.me.value[1],  # value used for selection
                   "left": self.insert_tree(node.left),
                   "right": self.insert_tree(node.right)}
        if new_doc["left"]:
            new_doc["left"] = new_doc["left"].inserted_id
        if new_doc["right"]:
            new_doc["right"] = new_doc["right"].inserted_id
        # print json.dumps(new_doc,4)
        return self.index_collection.insert_one(new_doc)

    def insert_indexed(self, roottree, data):
        # Receives AVL tree that index a list of elements Lewi's scheme

        # Each node contains a pair composed by the right side of a ciphertext
        # and the index of a related element in the list data (IndexNode)
        assert isinstance(roottree, AVLTree)
        assert type(data) in (list, tuple)

        # Adds data to the database and keep the ids
        data_indexes = []
        for i, item in enumerate(data):
            item["index"] = i
            data_indexes.append(self.insert(item))

        # Add indexes
        root = self.insert_tree(roottree)
        # Add a tag to the root node
        self.index_collection.update({"_id": root.inserted_id},
                                     {"$set": {"root": "1"}})

        return root

    def drop_collection(self):
        self.collection.drop()
        self.index_collection.drop()
        return

    ###########################################################################
    # Receives a list of keywords and verifies if any can be decrypted by some
    # sk in a list

    # The list of sks may have two levels. The first level represents a bitwise
    # AND, while the second one represents a bitwise OR.

    # i.e.
    # ["potatoes","hobbit",["frodo","sam"]]
    # this query should return results that contains ("frodo" or "sam") and
    # "potatoes" and "hobbit"

    def __eval_search(self, queries, keywords):
        assert type(queries) in [list, tuple]
        assert type(keywords) in [str, int, long, list, tuple]

        for query in queries:
            sk = query

            if type(sk) in [list, tuple]:
                # OR
                try:
                    for orsk in query:
                        if self.__exists(orsk, keywords):
                            raise StopLookingForThings()
                    return False
                except StopLookingForThings:
                    return True
                    continue
            else:
                # AND
                if not self.__exists(sk, keywords):
                    return False
                    continue

        return True

    # Receives a list of keywords and a sk.
    # Return True if there is any keyword in the list that matches with the sk.
    def __exists(self, sk, keywords):
        if all(type(keywords) in [list, tuple] for keywords in keywords):
            for keyword in keywords:
                # Must exist at least one
                pt = self.__ciphers["keyword"].decrypt(sk, keyword)
                if pt in ([1], (1,)):
                    return True
        else:
            keyword = keywords
            pt = self.__ciphers["keyword"].decrypt(sk, keyword)
            if pt in ([1], (1,)):
                return True
        return False

    # Returns all entries indexed from that node
    def __get_branch(self, node):
        entries = []
        if node is not None:
            entries.extend(self.collection.find({"_id": {"$in": node["index"]}}))
            entries.extend(self.__get_branch(self.index_collection.find_one({"_id": node["right"]})))
            entries.extend(self.__get_branch(self.index_collection.find_one({"_id": node["left"]})))
        return entries