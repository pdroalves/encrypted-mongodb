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
import pymongo
from pymongo import MongoClient
from .crypto import paillier
from .crypto import elgamal
from .crypto.ore import ORE
from .index.avltree import AVLTree
from .index.indexnode import IndexNode
from bson.json_util import dumps
from multiprocessing import Queue
from bson import ObjectId
import json
import time
import os
from itertools import chain,islice

class StopLookingForThings(Exception):
    pass


class SecMongo:
    ASCENDING = pymongo.ASCENDING
    DESCENDING = pymongo.DESCENDING
    RANGE_OP = 42
    EQUALITY_OP = 0
    GREATER_OP = 1
    LOWER_OP = -1

    client = None
    db = None
    collection = None

    __ciphers = {"references": None, "h_add": None, "h_mul": None}

    def __init__(self, add_cipher_param=None, url=None):
        assert url is None or type(url) == str

        # Connects to database
        if url:
            self.client = MongoClient(url)
        else:
            self.client = MongoClient()

        self.__ciphers["references"] = ORE
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
        script_dir = os.path.join(os.path.dirname(__file__), "scripts")
        scripts = filter(lambda x: x.endswith(".js"), os.listdir(script_dir))
        for script in scripts:
            with open(os.path.join(script_dir, script), "r") as js_file:
                setattr(self.db.system_js, script.strip(".js"),
                        "".join(js_file.readlines()))

    def set_collection(self, collection):
        assert type(collection) is str
        self.collection = self.db[collection]
        self.index_collection = self.db["references_"+collection]

    # Executes a single lookup operation.
    # 
    # return_ids: Return a list with ids, if True. Else, return a cursor.
    def find(self,
            index = None,
            relationship = 0,
            projection = None,
            iname = None,
            sort=False,
            return_ids = False):

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
        queue = Queue()
        queue.put(self.index_collection.find_one({"parent": None, "iname":iname}))
        result = []
        niterations = 0
        while queue.qsize() > 0:
            node = queue.get() # consume
            while node is None and queue.qsize() > 0:
                node = queue.get() # consume
            if node is None:
                break # End

            ctR = node["ctR"]  # b
            r = self.__ciphers["references"].compare(ctL, ctR)
            if relationship == 0: # Equality
                if r == 0:
                    # Found
                    # a == b
                    result.extend(node["references"])
                elif r == 1:
                    # a < b
                    if node["right"] is not None:
                        queue.put(self.index_collection.find_one(
                            {"iname_id": node["right"], "iname": iname})
                        )
                else:
                    assert r == -1
                    # a > b
                    if node["left"] is not None:
                        queue.put(self.index_collection.find_one(
                            {"iname_id": node["left"], "iname": iname})
                        )
            elif relationship == 1: # > than
                if r == 0 or r == -1:
                    if node["left"] is not None:
                        queue.put(self.index_collection.find_one(
                            {"iname_id": node["left"], "iname": iname})
                        )
                else:
                    assert r == 1
                    # Found
                    result.extend(node["references"])
                    if node["left"] is not None:
                        queue.put( self.index_collection.find_one(
                            {"iname_id": node["left"], "iname": iname}))
                    if node["right"] is not None:
                        queue.put( self.index_collection.find_one(
                            {"iname_id": node["right"], "iname": iname}))
            else: # < than
                assert relationship == -1
                if r == 0 or r == 1:
                    if node["right"] is not None:
                        queue.put( self.index_collection.find_one(
                            {"iname_id": node["right"], "iname": iname}))
                else:
                    assert r == -1
                    # Found
                    result.extend(node["references"])
                    if node["left"] is not None:
                        queue.put( self.index_collection.find_one(
                            {"iname_id": node["left"], "iname": iname}))
                    if node["right"] is not None:
                        queue.put( self.index_collection.find_one(
                            {"iname_id": node["right"], "iname": iname}))
            niterations = niterations + 1
        print "%d iterations to find the result" % niterations
        # print "Result: %d docs" % len(result)
        if return_ids:
            return result
        else:
            return self.collection.find({"_id": {"$in": result}}, projection = projection)

    def find_range(self,
            index = None,
            projection = None,
            iname = None,
            return_ids = False):

        if index is None:
            return self.collection.find()
        else:
            assert type(index) in (list, tuple) and len(index) == 2

        # Search by an index
        # This method expects an index value (the ctL)
        start_ctL, end_ctL = index 
        #  To search for elements with an attribute named "age" with a value
        #  between 30 and 40
        #
        #  The query MUST be encrypted
        # Get the tree root
        queue = Queue()
        queue.put(self.index_collection.find_one({"parent": None, "iname":iname}))
        result = []
        niterations = 0
        while queue.qsize() > 0:
            node = queue.get() # consume
            while node is None and queue.qsize() > 0:
                node = queue.get() # consume
            if node is None:
                break # End

            ctR = node["ctR"]  # b
            r_start = self.__ciphers["references"].compare(start_ctL, ctR)
            r_end = self.__ciphers["references"].compare(end_ctL, ctR)
            if r_start == 0:
                result.extend(node["references"])
                if node["right"] is not None:
                    queue.put( self.index_collection.find_one(
                        {"iname_id": node["right"], "iname": iname}))
            elif r_end == 0:
                result.extend(node["references"])
                if node["left"] is not None:
                    queue.put( self.index_collection.find_one(
                        {"iname_id": node["left"], "iname": iname}))
            elif r_start == -1 and r_end == 1: # in the interval
                result.extend(node["references"])
                if node["left"] is not None:
                    queue.put( self.index_collection.find_one(
                        {"iname_id": node["left"], "iname": iname}))
                if node["right"] is not None:
                    queue.put( self.index_collection.find_one(
                        {"iname_id": node["right"], "iname": iname}))
            elif r_start == 1 and r_end == 1:
                if node["right"] is not None:
                    queue.put( self.index_collection.find_one(
                        {"iname_id": node["right"], "iname": iname}))
            elif r_start == -1 and r_end == -1:
                if node["left"] is not None:
                    queue.put( self.index_collection.find_one(
                        {"iname_id": node["left"], "iname": iname}))

            niterations = niterations + 1
        print "%d iterations to find the result" % niterations
        # print "Result: %d docs" % len(result)
        if return_ids:
            return result
        else:
            return self.collection.find({"_id": {"$in": result}}, projection = projection)

    def find_nested(self, queries, return_ids = False):
        # Receives a sequence of operations that should be executed.
        # Each operation works on the outcome of the previous.
        # 
        # To find someone with age greater than 5 and with brown hair:
        # 
        # [ {"age", 1, 5}, {"hair", 0, "brown"}]
        # 
        query_results = []

        for i, query in enumerate(queries):
            iname, relationship, value = query

            if relationship == self.RANGE_OP:
                # range
                # The outcome for this condition
                query_results.append(self.find_range(
                    index = value,
                    projection = ["_id"],
                    iname = iname,
                    return_ids = True
                ))
            else:
                # The outcome for this condition
                query_results.append(self.find(
                    index = value,
                    iname = iname,
                    relationship = relationship,
                    projection = ["_id"],
                    return_ids = True
                ))

        result = []
        for query_result in query_results:
            if len(result) == 0:
                result.extend(query_result)
            else:
                result = set(result).intersection(set(query_result))
        if return_ids:
            return list(result)
        else:
            return self.collection.find({"_id":{"$in": list(result)}})

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

    def insert_many(self, docs):
        return self.collection.insert_many(docs, ordered = False, bypass_document_validation = True)

    def print_index(self, node=None, spaces=0):
        if(not node):
            node = self.index_collection.find_one({"root": "1"})
            print("Root Index: ", node["index"])
        if(node["right"]):
            print(" " * spaces, "right", self.print_index(self.index_collection.find_one({"iname_id": node["right"]}), spaces=spaces+4))
        if(node["left"]):
            print(" " * spaces, "left", self.print_index(self.index_collection.find_one({"iname_id": node["left"]}), spaces=spaces+4))
        return node["index"]

    #
    # Receives an encrypted node and inserts it in the avl-tree index
    # 
    # value: the inserted enc_doc 
    # inserted_index: the encrypted node
    # iname: index collection name
    #
    def insert_index(self, index_ctL, index_ctR, inserted_index, iname):
        # We use the index_ctL to look for the position in the index to add a
        # pointer to inserted_index

        # Gets the root node
        node = self.index_collection.find_one({"parent": None, "iname": iname})
        leaf_id = self.index_collection.count()
        if not node:
            # There is no root. The index tree is empty.
            return self.index_collection.insert_one({
                "references": [inserted_index],
                "ctR": index_ctR,
                "parent": None,
                "left": None,
                "right": None,
                "iname": iname, 
                "height": 1
            })
        # Looks for a leaf to become parent of this index
        while node is not None:
            ctR = node["ctR"]# Given a node, compares to the target
            r = self.__ciphers["references"].compare(index_ctL, ctR)

            if r == 0:
                # The node already exists in the tree
                # Adds the pointed value to the "references" set
                self.index_collection.update(
                    {"iname_id": node["iname_id"]},
                    {"$addToSet": {"references": inserted_index}}
                )
                return node
                
            elif r == 1:
                # index is bigger than this node.
                # Move to the righty node
                if node["right"] is None:
                    # There is no node on the right. This is a leaf.
                    # Add the target as the righty node.
                    new = self.index_collection.insert_one({
                        "iname_id": leaf_id,
                        "references": [inserted_index],
                        "ctR": index_ctR,
                        "parent": node["iname_id"],
                        "left": None,
                        "right": None,
                        "iname": iname, 
                        "height": 1
                    })
                    self.index_collection.update(
                        {"iname_id": node["iname_id"]},
                        {"$set": {"right": leaf_id}}
                    )
                    break
                else:
                    # There is a node on the right.
                    node = self.index_collection.find_one(
                        {"iname_id": node["right"], "iname": iname}
                    )
            elif r == -1:
                # index is lower than this node.
                if node["left"] is None:
                    # This is a leaf.
                    # Add left index
                    new = self.index_collection.insert_one({
                        "iname_id": leaf_id,
                        "references": [inserted_index],
                        "ctR": index_ctR,
                        "parent": node["iname_id"],
                        "left": None,
                        "right": None,
                        "iname": iname, 
                        "height": node["height"] + 1
                    })
                    self.index_collection.update(
                        {"iname_id": node["iname_id"]},
                        {"$set": {"left": leaf_id}}
                    )
                    break
                else:
                    node = self.index_collection.find_one(
                        {"iname_id": node["left"], "iname": iname}
                    )
        # self.run_scripts()
        return new
    
    # 
    # build the index for a collection of encrypted documents on memory
    # returns the index as a list
    # 
    def mem_build_index(self, enc_docs, iname):
        icollection = []

        # There is no root. The index tree is empty.
        # Inserts the first document as the root
        enc_doc = enc_docs[0]
        index_ctL = enc_doc[iname][0]
        index_ctR = enc_doc[iname][1]
        inserted_index = enc_doc["inserted_index"]
        icollection.append({
                "iname_id": 0,
                "references": [inserted_index],
                "ctR": index_ctR,
                "parent": None,
                "left": None,
                "right": None,
                "iname": iname, 
                "height": 1
            })
        h = 1
        start = time.time()
        count = 0
        for i, enc_doc in enumerate(enc_docs[1:]):
            h = max(h, icollection[-1]["height"])
            if i % 100 == 0:
                # print "%d \ %d - height: %d" % (i, len(enc_docs[1:]), self.__mem_get_tree_height(icollection, iname))
                print "%d \ %d - height: %d" % (i, len(enc_docs[1:]), h)
                print "%f doc/s" % ((i - count) / (time.time() - start))
                start = time.time()
                count = i
            
            index_ctL = enc_doc[iname][0]
            index_ctR = enc_doc[iname][1]
            inserted_index = enc_doc["inserted_index"]
                
            # Looks for a leaf to become parent of this index
            node = icollection[0]
            root = icollection[0]
            self.mem_balance_node(icollection, icollection[-1])
            while node is not None:
                ctR = node["ctR"]# Given a node, compares to the target
                r = self.__ciphers["references"].compare(index_ctL, ctR)

                if r == 0:
                    # The node already exists in the tree
                    # Adds the pointed value to the "references" set
                    icollection[icollection.index(node)]["references"].append(
                        inserted_index
                    )
                    break
                elif r == 1:
                    # index is bigger than this node.
                    # Move to the righty node
                    if node["right"] is None:
                        # There is no node on the right. This is a leaf.
                        # Add the target as the righty node.
                        leaf_id = len(icollection)
                        icollection.append({
                            "iname_id": leaf_id,
                            "references": [inserted_index],
                            "ctR": index_ctR,
                            "parent": node["iname_id"],
                            "left": None,
                            "right": None,
                            "iname": iname, 
                            "height": node["height"] + 1
                        })
                        icollection[icollection.index(node)]["right"] = leaf_id
                        break
                    else:
                        # There is a node on the right.
                        node = [x for x in icollection if x["iname_id"] == node["right"]][0]
                elif r == -1:
                    # index is lower than this node.
                    if node["left"] is None:
                        # This is a leaf.
                        # Add left index
                        leaf_id = len(icollection)
                        icollection.append({
                            "iname_id": leaf_id,
                            "references": [inserted_index],
                            "ctR": index_ctR,
                            "parent": node["iname_id"],
                            "left": None,
                            "right": None,
                            "iname": iname, 
                            "height": node["height"] + 1
                        })
                        icollection[icollection.index(node)]["left"] = leaf_id
                        break
                    else:
                        node = [x for x in icollection if x["iname_id"] == node["left"]][0]
        return icollection

    # 
    # build the index for a collection of encrypted documents on memory
    # returns the index as a list
    # 
    # https://stackoverflow.com/questions/1295285/efficient-algorithm-for-building-an-avl-tree-from-large-collection
    # 
    def mem_enc_ordered_build_index(self, enc_docs, iname):
        ore_compare = lambda x, y: self.__ciphers["references"].compare(x[0],y[1])

        print "Will sort enc_docs"
        start = time.time()
        # import pdb;pdb.set_trace()
        enc_docs.sort(cmp = lambda x, y: self.__ciphers["references"].compare(x[iname]["index"][0],y[iname]["index"][1]))
        end = time.time()
        print "Done in %ds (%f doc/s)" % (end - start, len(enc_docs)/float(end-start))

        print "Will group enc_docs."
        start = time.time()
        grouped_enc_docs = []
        for enc_doc in enc_docs:
            if len(grouped_enc_docs) > 0 and self.__ciphers["references"].compare(enc_doc[iname]["index"][0], grouped_enc_docs[-1][iname]["index"][1]) == 0:
                # Are equal. Group.
                assert isinstance(enc_doc["_id"], ObjectId) or type(enc_doc["_id"]) == int
                grouped_enc_docs[-1][iname]["inserted_indexes"].append(enc_doc["_id"])
            else:
                # New doc
                assert isinstance(enc_doc["_id"], ObjectId) or type(enc_doc["_id"]) == int
                enc_doc[iname]["inserted_indexes"] = [enc_doc["_id"]]
                grouped_enc_docs.append(enc_doc)

        end = time.time()
        print "Done in %ds (%f doc/s)" % (end - start, len(enc_docs)/float(end-start))
        print "grouped_enc_docs: %d" % len(grouped_enc_docs)
        icollection = []
        self.__mem_enc_ordered_build_index_aux(icollection, grouped_enc_docs, 0, len(grouped_enc_docs)-1, iname)
        return icollection

    # L and R are indexes in enc_docs
    def __mem_enc_ordered_build_index_aux(self, icollection, enc_docs, L, R, iname,height = 1, parent_iname_id = None):

        if (L-R) == 0:
            #   if(L == R)
            #     return Node_new(key[L], value[L]);
            enc_doc = enc_docs[L]
            index_ctL = enc_doc[iname]["index"][0]
            index_ctR = enc_doc[iname]["index"][1]
            inserted_indexes = enc_doc[iname]["inserted_indexes"]
            iname_id = len(icollection)
            icollection.append({
                "iname_id": iname_id,
                "references": inserted_indexes,
                "ctR": index_ctR,
                "parent": parent_iname_id,
                "left": None,
                "right": None,
                "iname": iname, 
                "height": height + 1
            })
            return iname_id
        elif (L-R) == 1:
            #   if(L+1 == R) {
            #     Node *left = Node_new(key[L], value[L]);
            #     Node *right = Node_new(key[R], value[R]);
            #     left->tree.avl_right = right;
            #     left->tree.avl_height = 1;
            #     return left;
            #   }
            left = enc_docs[0]
            right = enc_docs[1]

            index_left_ctR = left[iname]["index"][1]
            index_right_ctR = right[iname]["index"][1]

            inserted_left_index = left[iname]["inserted_indexes"]
            inserted_right_index = right[iname]["inserted_indexes"]

            right_iname_id = len(icollection)
            icollection.append({
                "iname_id": right_iname_id,
                "references": inserted_right_index,
                "ctR": index_right_ctR,
                "parent": None,
                "left": None,
                "right": None,
                "iname": iname, 
                "height": height+2
            })
            left_iname_id = len(icollection)
            icollection.append({
                "iname_id": left_iname_id,
                "references": inserted_left_index,
                "ctR": index_left_ctR,
                "parent": parent_iname_id,
                "left": None,
                "right": right_iname_id,
                "iname": iname, 
                "height": height+1
            })
            icollection[-2]["parent"] = left_iname_id
            return left_iname_id
        else:
            #   // more than two nodes
            #   M = L + (R-L)/2;
            #   middle = Node_new(key[M], value[M]);
            #   middle->tree.avl_left = tree_build(key, value, L, M-1);
            #   middle->tree.avl_right = tree_build(key, value, M+1, R);
            #   lh = middle->tree.avl_left->tree.avl_height;
            #   rh = middle->tree.avl_right->tree.avl_height;
            #   middle->tree.avl_height = 1 + (lh > rh ? lh:rh);
            #   return middle;
            # }
            
            M_id = L + (R-L)/2
            M = enc_docs[M_id]
            index_ctL, index_ctR = M[iname]["index"]
            inserted_indexes = M[iname]["inserted_indexes"]
            middle_iname_id = len(icollection)

            # Add to the collection
            middle = {
                    "iname_id": middle_iname_id,
                    "references": inserted_indexes,
                    "ctR": index_ctR,
                    "parent": parent_iname_id,
                    "left": None,
                    "right": None,
                    "iname": iname, 
                    "height": height+1
                }
            icollection.append(middle)

            left_iname_id = self.__mem_enc_ordered_build_index_aux(
                        icollection,
                        enc_docs,
                        L,
                        M_id-1,
                        iname,
                        height+1,
                        middle_iname_id
                        )
            right_iname_id = self.__mem_enc_ordered_build_index_aux(
                        icollection,
                        enc_docs,
                        M_id+1,
                        R,
                        iname,
                        height+1,
                        middle_iname_id
                        )
            # Update
            middle["left"] =  left_iname_id
            middle["right"] = right_iname_id
            left_height = 1
            right_height = 1
            # left_height = self.__mem_get_tree_height(icollection, middle["left"])["height"]
            # right_height = self.__mem_get_tree_height(icollection, middle["right"])["height"]
            middle["height"] = 1 + max(left_height, right_height)

            return middle_iname_id



    # 
    # build the index for a collection of plaintext documents on memory
    # returns the index as a list
    # 
    def mem_ordered_build_index(self, docs, iname, client):
        print "[%s] - Will sort docs" % iname
        start = time.time()
        docs.sort(key = lambda x: x[iname])
        end = time.time()
        print "[%s] - Done in %ds (%f doc/s)" % (iname, end - start, len(docs)/float(end-start))

        print "[%s] - Will group docs." % iname
        start = time.time()
        grouped_docs = []
        for doc in docs:
            if len(grouped_docs) > 0 and doc[iname] == grouped_docs[-1][iname]:
                # Are equal. Group.
                assert isinstance(doc["_id"], ObjectId) or type(doc["_id"]) in [long, int]
                grouped_docs[-1]["inserted_indexes"].append(doc["_id"])
            else:
                # New doc
                assert isinstance(doc["_id"], ObjectId) or type(doc["_id"]) in [long, int]
                grouped_doc = dict(doc)
                # doc.pop("_id")
                
                grouped_doc["inserted_indexes"] = [grouped_doc["_id"]]
                grouped_docs.append(grouped_doc)

        end = time.time()
        print "[%s] - Done in %ds (%f doc/s)" % (iname, end - start, len(docs)/float(end-start))
        print "[%s] - grouped_docs: %d" % (iname, len(grouped_docs))
        icollection = []
        start = time.time()
        self.__mem_ordered_build_index_aux(icollection, grouped_docs, 0, len(grouped_docs)-1, iname, client)
        end = time.time()
        print "[%s] - Done in %ds (%f doc/s)" % (iname, end - start, len(docs)/float(end-start))
        return icollection

    # L and R are indexes in enc_docs
    def __mem_ordered_build_index_aux(self, icollection, docs, L, R, iname, client, height = 1, parent_iname_id = None):

        if (L-R) == 0:
            #   if(L == R)
            #     return Node_new(key[L], value[L]);
            doc = docs[L]
            index_ctR = client.get_ctR(doc[iname])
            inserted_indexes = doc["inserted_indexes"]
            iname_id = len(icollection)
            icollection.append({
                "iname_id": iname_id,
                "references": inserted_indexes,
                "ctR": index_ctR,
                "parent": parent_iname_id,
                "left": None,
                "right": None,
                "iname": iname, 
                "height": height + 1
            })
            return iname_id
        elif (L-R) == 1:
            #   if(L+1 == R) {
            #     Node *left = Node_new(key[L], value[L]);
            #     Node *right = Node_new(key[R], value[R]);
            #     left->tree.avl_right = right;
            #     left->tree.avl_height = 1;
            #     return left;
            #   }
            left = docs[0]
            right = docs[1]

            index_left_ctR = client.get_ctR(left[iname])
            index_right_ctR = client.get_ctR(right[iname])

            inserted_left_index = left["inserted_indexes"]
            inserted_right_index = right["inserted_indexes"]

            right_iname_id = len(icollection)
            icollection.append({
                "iname_id": right_iname_id,
                "references": inserted_right_index,
                "ctR": index_right_ctR,
                "parent": None,
                "left": None,
                "right": None,
                "iname": iname, 
                "height": height+2
            })
            left_iname_id = len(icollection)
            icollection.append({
                "iname_id": left_iname_id,
                "references": inserted_left_index,
                "ctR": index_left_ctR,
                "parent": parent_iname_id,
                "left": None,
                "right": right_iname_id,
                "iname": iname, 
                "height": height+1
            })
            icollection[-2]["parent"] = left_iname_id
            return left_iname_id
        else:
            #   // more than two nodes
            #   M = L + (R-L)/2;
            #   middle = Node_new(key[M], value[M]);
            #   middle->tree.avl_left = tree_build(key, value, L, M-1);
            #   middle->tree.avl_right = tree_build(key, value, M+1, R);
            #   lh = middle->tree.avl_left->tree.avl_height;
            #   rh = middle->tree.avl_right->tree.avl_height;
            #   middle->tree.avl_height = 1 + (lh > rh ? lh:rh);
            #   return middle;
            # }
            
            M_id = L + (R-L)/2
            M = docs[M_id]
            index_ctR = client.get_ctR(M[iname])
            inserted_indexes = M["inserted_indexes"]
            middle_iname_id = len(icollection)

            # Add to the collection
            middle = {
                    "iname_id": middle_iname_id,
                    "references": inserted_indexes,
                    "ctR": index_ctR,
                    "parent": parent_iname_id,
                    "left": None,
                    "right": None,
                    "iname": iname, 
                    "height": height+1
                }
            icollection.append(middle)

            left_iname_id = self.__mem_ordered_build_index_aux(
                        icollection,
                        docs,
                        L,
                        M_id-1,
                        iname,
                        client,
                        height+1,
                        middle_iname_id
                        )
            right_iname_id = self.__mem_ordered_build_index_aux(
                        icollection,
                        docs,
                        M_id+1,
                        R,
                        iname,
                        client,
                        height+1,
                        middle_iname_id
                        )
            # Update
            middle["left"] =  left_iname_id
            middle["right"] = right_iname_id
            left_height = 1
            right_height = 1
            # left_height = self.__mem_get_tree_height(icollection, middle["left"])["height"]
            # right_height = self.__mem_get_tree_height(icollection, middle["right"])["height"]
            middle["height"] = 1 + max(left_height, right_height)

            return middle_iname_id
    
    def __chunks(self, iterable, size=10000):
        iterator = iter(iterable)
        for first in iterator:
            yield chain([first], islice(iterator, size - 1))
    #
    # Receives an index built on memory and inserts in the DB
    def insert_mem_tree(self, iname_index):
        for c in self.__chunks(iname_index):
            self.index_collection.insert_many(c, ordered = False, bypass_document_validation = True)

    def run_scripts(self, new):
        if isinstance(new, pymongo.results.InsertOneResult):
            print "Rebalancing... %s" % new.inserted_id
            self.db.system_js.update_height(self.index_collection.name,
                                            new.inserted_id)
            self.db.system_js.rebalance_avl(self.index_collection.name,
                                            new.inserted_id)
        else:
            print "Rebalancing... %s" % new["_id"]
            self.db.system_js.update_height(self.index_collection.name,
                                            new["_id"])
            self.db.system_js.rebalance_avl(self.index_collection.name,
                                            new["_id"])
            # self.balance_node(self.index_collection.find_one({"parent": None}))

    def balance_node(self, node):
        if node:
            left = self.index_collection.find_one({"iname_id": node["left"]})
            left_balance, left_height = self.balance_node(left)

            right = self.index_collection.find_one({"iname_id": node["right"]})
            right_balance, right_height = self.balance_node(right)

            node = self.index_collection.find_one(
                {"iname_id": node["iname_id"]}
            )
            left = self.index_collection.find_one({"iname_id": node["left"]})
            right = self.index_collection.find_one({"iname_id": node["right"]})

            local_balance = (right_height - left_height)
            if local_balance not in [-1, 0, 1]:
                print("unbalance")
                if local_balance > 0:
                    parent = self.index_collection.find_one(
                        {"iname_id": right["iname_id"]}
                    )
                    if right_balance < 0:
                        self.right_rotate(right)
                        node = self.index_collection.find_one(
                            {"iname_id": node["iname_id"]}
                        )
                        parent = self.index_collection.find_one(
                            {"iname_id": right["left"]}
                        )
                    self.left_rotate(node)
                elif local_balance < 0:
                    parent = self.index_collection.find_one(
                        {"iname_id": left["iname_id"]}
                    )
                    if left_balance > 0:
                        self.left_rotate(left)
                        node = self.index_collection.find_one(
                            {"iname_id": node["iname_id"]}
                        )
                        parent = self.index_collection.find_one(
                            {"iname_id": left["right"]}
                        )
                    self.right_rotate(node)
                return self.balance_node(parent)

            return local_balance, max(left_height, right_height) + 1
        else:
            return 0, 0

    def right_rotate(self, node):
        left = self.index_collection.find_one({"iname_id": node["left"]})
        # Set original left child"s right child parent to node.
        if(left["right"]):
            self.index_collection.update(
                {"_id": left["right"]},
                {"$set": {"parent": node["_id"]}}
            )
        # Set original parent child to left child of node.
        if(node["parent"]):
            parent = self.index_collection.find_one({"iname_id": node["parent"]})
            side = "left" if parent["left"] == node["_id"] else "right"
            if side == "left":
                self.index_collection.update(
                    {"_id": parent["_id"]},
                    {"$set": {"left": left["_id"]}}
                )
            elif side == "right":
                self.index_collection.update(
                    {"_id": parent["_id"]},
                    {"$set": {"right": left["_id"]}}
                )
        # Set orginal left"s parent to node"s original parent.
        self.index_collection.update(
            {"_id": left["_id"]},
            {"$set": {"parent": node["parent"], "right": node["_id"]}}
        )
        # Set node"s left child to left"s original right child update parent of
        # node to original left child.
        self.index_collection.update(
            {"_id": node["_id"]},
            {"$set": {"left": left["right"], "parent": left["_id"]}}
        )

    def left_rotate(self, node):
        right = self.index_collection.find_one({"iname_id": node["right"]})
        # Set original left child"s right child parent to node.
        if(right["left"]):
            self.index_collection.update(
                {"_id": right["left"]},
                {"$set": {"parent": node["_id"]}}
            )
        # Set original parent child to right child of node.
        if(node["parent"]):
            parent = self.index_collection.find_one({"iname_id": node["parent"]})
            side = "left" if parent["left"] == node["_id"] else "right"
            if side == "left":
                self.index_collection.update(
                    {"_id": parent["_id"]},
                    {"$set": {"left": right["_id"]}}
                )
            elif side == "right":
                self.index_collection.update(
                    {"_id": parent["_id"]},
                    {"$set": {"right": right["_id"]}}
                )

        # Set orginal right"s parent to node"s original parent.
        self.index_collection.update(
            {"_id": right["_id"]},
            {"$set": {"parent": node["parent"], "left": node["_id"]}}
        )
        # Set node"s right child to right"s original right child update parent
        # of node to original right child.
        self.index_collection.update(
            {"_id": node["_id"]},
            {"$set": {"right": right["left"], "parent": right["_id"]}}
        )

    def mem_balance_node(self, mem_index, node):
        if node:
            # sanity test
            assert node["iname_id"] != node["left"]
            assert node["iname_id"] != node["right"]
            # Recursively walks through the tree until the leafs.
            left = self.__mem_get_node_by_iname_id(mem_index, node["left"])
            left_balance, left_height = self.mem_balance_node(mem_index, left)

            right = self.__mem_get_node_by_iname_id(mem_index, node["right"])
            right_balance, right_height = self.mem_balance_node(mem_index, right)

            # Get the required references
            # We ask for it again because the right/left node may have changed,
            # as well as the node itself
            node = self.__mem_get_node_by_iname_id(mem_index, node["iname_id"])
            left = self.__mem_get_node_by_iname_id(mem_index, node["left"])
            right = self.__mem_get_node_by_iname_id(mem_index, node["right"])

            local_balance = (right_height - left_height)
            if local_balance not in [-1, 0, 1]:
                # import pdb;pdb.set_trace()
                print("unbalance")
                if local_balance > 0:
                    parent = self.__mem_get_node_by_iname_id(mem_index, right["iname_id"])
                    if right_balance < 0:
                        self.mem_right_rotate(mem_index, right)
                        node = self.__mem_get_node_by_iname_id(mem_index, node["iname_id"])
                        parent = self.__mem_get_node_by_iname_id(mem_index, right["left"])

                    self.mem_left_rotate(mem_index, node)
                elif local_balance < 0:
                    parent = self.__mem_get_node_by_iname_id(mem_index, left["iname_id"])
                    if left_balance > 0:
                        self.mem_left_rotate(mem_index, left)
                        node = self.__mem_get_node_by_iname_id(mem_index, node["iname_id"])
                        parent = self.__mem_get_node_by_iname_id(mem_index, left["right"])
                    self.mem_right_rotate(mem_index, node)
                return self.mem_balance_node(mem_index, parent)

            return local_balance, max(left_height, right_height) + 1
        else:
            return 0, 0

    def mem_right_rotate(self, mem_index, node):
        left = self.__mem_get_node_by_iname_id(mem_index, node["left"])
        # Set original left child"s right child parent to node.
        if(left["right"]):
            self.__mem_update_node_by_iname_id(
                mem_index,
                left["right"],
                "parent",
                node["iname_id"])
        # Set original parent child to left child of node.
        if(node["parent"]):
            parent = self.__mem_get_node_by_iname_id(mem_index, node["parent"])
            side = "left" if parent["left"] == node["iname_id"] else "right"
            if side == "left":
                self.__mem_update_node_by_iname_id(
                    mem_index,
                    parent["iname_id"],
                    "left",
                    left["iname_id"])
            elif side == "right":
                self.__mem_update_node_by_iname_id(
                    mem_index,
                    parent["iname_id"],
                    "right",
                    left["iname_id"])
        # Set orginal left"s parent to node"s original parent.
        self.__mem_update_node_by_iname_id(
            mem_index,
            left["iname_id"],
            "parent",
            node["parent"])
        self.__mem_update_node_by_iname_id(
            mem_index,
            left["iname_id"],
            "right",
            node["iname_id"])
        # Set node"s left child to left"s original right child update parent of
        # node to original left child.
        self.__mem_update_node_by_iname_id(
            mem_index,
            node["iname_id"],
            "parent",
            left["iname_id"])
        self.__mem_update_node_by_iname_id(
            mem_index,
            node["iname_id"],
            "left",
            left["right"])

    def mem_left_rotate(self, mem_index, node):
        right = self.__mem_get_node_by_iname_id(mem_index, node["right"])
        # Set original left child"s right child parent to node.
        if(right["left"]):
            self.__mem_update_node_by_iname_id(
                mem_index,
                right["left"],
                "parent",
                node["iname_id"])
        # Set original parent child to right child of node.
        if(node["parent"]):
            parent = self.__mem_get_node_by_iname_id(mem_index, node["parent"])
            side = "left" if parent["left"] == node["iname_id"] else "right"
            if side == "left":
                self.__mem_update_node_by_iname_id(
                    mem_index,
                    parent["iname_id"],
                    "left",
                    right["iname_id"])
            elif side == "right":
                self.__mem_update_node_by_iname_id(
                    mem_index,
                    parent["iname_id"],
                    "right",
                    right["iname_id"])

        # Set orginal right"s parent to node"s original parent.
        self.__mem_update_node_by_iname_id(
            mem_index,
            right["iname_id"],
            "parent",
            node["parent"])
        self.__mem_update_node_by_iname_id(
            mem_index,
            right["iname_id"],
            "left",
            node["iname_id"])
        # Set node"s right child to right"s original right child update parent
        # of node to original right child.
        self.__mem_update_node_by_iname_id(
            mem_index,
            node["iname_id"],
            "parent",
            right["iname_id"])
        self.__mem_update_node_by_iname_id(
            mem_index,
            node["iname_id"],
            "right",
            right["left"])

    def drop_collection(self):
        self.collection.drop()
        self.index_collection.drop()
        return

    def __mem_get_node_by_iname_id(self, mem_index, iname_id):
        if iname_id is None:
            return None
        assert type(iname_id) == int

        result = [x for x in mem_index if x["iname_id"] == iname_id]
        if result:
            assert len(result) == 1
            return result[0]
        else:
            return None
    
    # Get the element of mem_index with a certain iname_id and changes the related attribute
    def __mem_update_node_by_iname_id(self, mem_index, iname_id, attribute, value):
        target = self.__mem_get_node_by_iname_id(mem_index, iname_id)            
        assert target is not None
        assert iname_id is not value
        mem_index[mem_index.index(target)][attribute] = value

    def __mem_get_tree_height(self, mem_index, iname):
        root = [x for x in mem_index if x["parent"] == None and x["iname"] == iname][0]
        return self.__mem_get_tree_height_aux(mem_index, root)

    def __mem_get_tree_height_aux(self, mem_index, node):
        if node is None:
            return 1
        else:
            return max(
                node["height"],
                self.__mem_get_tree_height_aux(
                    mem_index,
                    self.__mem_get_node_by_iname_id(mem_index, node["right"])
                    ),
                self.__mem_get_tree_height_aux(
                    mem_index,
                    self.__mem_get_node_by_iname_id(mem_index, node["left"])
                    )
                )

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

    # Returns all records from the left and right subtrees
    def __get_branch(self, node, projection = None):
        records = []
        if node is not None:
            if projection:
                records.extend(self.collection.find({"_id": {"$in": node["references"]}}, projection = projection))
                records.extend(self.__get_branch(self.index_collection.find_one({"iname_id": node["right"]}), projection = projection))
                records.extend(self.__get_branch(self.index_collection.find_one({"iname_id": node["left"]}), projection = projection))
            else:
                records.extend(self.collection.find({"_id": {"$in": node["references"]}}))
                records.extend(self.__get_branch(self.index_collection.find_one({"iname_id": node["right"]})))
                records.extend(self.__get_branch(self.index_collection.find_one({"iname_id": node["left"]})))
        return records
