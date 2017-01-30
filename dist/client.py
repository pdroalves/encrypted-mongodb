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
# This class is a conceptual implementation of the behavior that a standard
# user should adopt to interact with mongodb-secure

from secmongo.crypto import cipher as dummy_cipher
from secmongo.crypto import aes
from secmongo.crypto import paillier
from secmongo.crypto import elgamal
from secmongo.crypto.ore import ORE
from datetime import timedelta
from datetime import date
import struct


def oreEncoder(x):
    x_enc = [struct.pack(">I", ord(x)) for x in x]
    return int("".join(x_enc).encode("hex"), 16)


def decode(x):
    x_dec = [chr(int(x[8 * i:8 * (i + 1)], 16)) for i in range(len(x) / 8)]
    return "".join(x_dec)


class Client:
    __supported_attr_types = ["static", "index", "h_add", "h_mul",
                              "do_nothing"]
    __mapped_attr = {}
    ciphers = {}

    def __init__(self, keys):

        # Initializes all ciphers
        AES = aes.AES()
        AES.add_to_private_key("key", keys["AES"])

        Paillier = paillier.Paillier()
        Paillier.add_to_private_key("lambda",
                                    keys["Paillier"]["priv"]["lambda"])
        Paillier.add_to_public_key("n", keys["Paillier"]["pub"]["n"])
        Paillier.add_to_public_key("g", keys["Paillier"]["pub"]["g"])

        ElGamal = elgamal.ElGamal()
        ElGamal.add_to_public_key("p", keys["ElGamal"]["pub"]["p"])
        ElGamal.add_to_public_key("alpha", keys["ElGamal"]["pub"]["alpha"])
        ElGamal.add_to_public_key("beta", keys["ElGamal"]["pub"]["beta"])
        ElGamal.add_to_private_key("d", keys["ElGamal"]["priv"]["d"])

        ore = ORE()
        ore.keygen()

        Dummy = dummy_cipher.Cipher()

        self.ciphers = {"static": AES,
                        "index": ore,
                        "h_add": Paillier,
                        "h_mul": ElGamal,
                        "do_nothing": Dummy}

    # Generates all keys
    @staticmethod
    def keygen():
        keys = {}
        keys["AES"] = aes.AES.keygen("password")
        keys["ORE"] = aes.AES.keygen("password")
        keys["Paillier"] = paillier.Paillier.keygen()
        keys["ElGamal"] = elgamal.ElGamal.keygen()

        return keys

    # Encrypts a query

    # pt: plaintex
    # kind: defines the purpose for which the document should be encrypted
    # parent: the parent key
    def encrypt(self, pt, kind="store", parent=None):
        global oreEncoder
        assert type(pt) == dict
        ciphers = self.ciphers
        result = {}
        # finds the lef
        for key in pt:
            if type(pt[key]) == dict:
                result[key] = self.encrypt(pt[key], kind=kind, parent=key)
            elif parent in ["$inc", "$dec", "$set"]:
                # Update query
                op_kind = self.__mapped_attr[key]

                cipher = ciphers[op_kind]
                result[key] = cipher.encrypt(pt[key])

            elif key == "$in":
                if type(pt[key]) not in [list, tuple]:
                    result[key] = list(pt[key])
                # Inside
                op_kind = self.__mapped_attr[parent]
                cipher = ciphers[op_kind]

                # Encrypts all items
                result[key] = []
                for value in pt[key]:
                    ct = cipher.encrypt(value)
                    result[key].append(ct)

            elif self.__mapped_attr[key] == "index":
                # Encrypts as a index

                # Currently this only supports database records with
                # a single index element

                op_kind = "index"
                cipher = ciphers[op_kind]

                # value = oreEncoder(pt[key]) if len(pt[key]) > 0 else "0"
                ct = cipher.encrypt(pt[key])
                result["index"] = ct[1]

                # Encrypts as static
                cipher = ciphers["static"]
                result[key] = cipher.encrypt(pt[key])
            else:
                if kind in ["search", "update"]:
                    continue
                op_kind = self.__mapped_attr[key]
                cipher = ciphers[op_kind]
                result[key] = cipher.encrypt(pt[key])
        return result

    # Decrypts the return of a query
    def decrypt(self, ct):
        assert type(ct) == dict

        ciphers = self.ciphers

        result = {}
        # finds the lef
        for key in ct:
            if key == "index":
                # There is no feasible to decrypt a index
                continue
            elif key == "_id":
                result[key] = ct[key]
            elif type(ct[key]) == dict:
                result[key] = self.decrypt(ct[key])
            elif type(ct[key]) in [tuple, list]:
                op_kind = self.__mapped_attr[key]
                cipher = ciphers[op_kind]

                for value in ct[key]:
                    pt = cipher.decrypt(value)
                    result[self.__keyword_attr].append(pt)
            elif self.__mapped_attr[key] == "index":
                # Decrypt the static version
                op_kind = "static"
                cipher = ciphers[op_kind]

                pt = cipher.decrypt(ct[key])
                result[key] = pt
            else:
                op_kind = self.__mapped_attr[key]
                cipher = ciphers[op_kind]

                pt = cipher.decrypt(ct[key])
                result[key] = pt

        return result

    def get_ctL(self, target):
        # Returns the left encryption of some target
        cipher = self.ciphers["index"]
        return cipher.encrypt(target)[0]

    def get_supported_attr_types(self):
        return tuple(self.__supported_attr_types)

    # Maps an attribute to one of those supported fields
    def set_attr(self, field, t):
        assert type(field) == str
        assert type(t) == str
        assert t in self.__supported_attr_types

        self.__mapped_attr[field] = t
