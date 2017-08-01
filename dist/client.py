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
        self.keys = keys
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
        # ore.keygen()
        ore.sk = (10, ((3223259985674656667L, 2545841574562126603L), (6648204193183595420L, 947396505544782198L), (10262699335115293910L, 12481950425502523357L), (11157155043314648013L, 10949369431025463995L), (11449385253512302172L, 3737047598145425793L), (14849964137264564366L, 6477956134748224053L), (8516286119396656814L, 5040449266868623151L), (6519988066647821184L, 260632987663511989L), (8526636966755636671L, 3722214930938200720L), (9203381554123655654L, 8945572252108388435L), (17817520749984642683L, 14187317918651806955L), (1L, 4990873L), (0L, 139930034503680L), (0L, 0L), (0L, 139932614805264L), (139930034503690L, 4959270L)), 10, ((18339622188540201800L, 13460209471301406482L), (6609222744464408615L, 734129833637601795L), (4171575670374974697L, 9450853066432056315L), (3410519472982782108L, 2694487752145932959L), (14257035632522015546L, 5112437236391459009L), (940852219221491269L, 2912186625399794906L), (16928794174384356480L, 12401838118053217345L), (8907847841761730801L, 6049779216749759531L), (15853460724620576482L, 8079141652577108643L), (7840338763158696984L, 4556332979460618291L), (5870209929380976196L, 2407680133169321191L), (0L, 5105312L), (139932614810752L, 9838200L), (139932661444688L, 139932614810752L), (0L, 4918451L), (10L, 4863747L)))
        ore.n = 32
        ore.k = 8
        print ore.sk

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
        keys["ORE"] = keys["AES"]
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
