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

def is_int(n):
    try:
        int(n)
        return True
    except:
        return False

class Client:
    __supported_attr_types = ["static", "index", "h_add", "h_mul",
                              "do_nothing"]
    # 
    # A map of attributes that should be encrypted as a particular class
    # for instance, {static:[name, age, address, count], h_add:[count]} will
    # tag attributes name, age, address and count to be encrypted as static and
    # count to be encrypted also as h_add
    # 
    __mapped_attr = {}

    # Ciphers
    ciphers = {}

    def __init__(self, keys):
        self.keys = keys
        # Initializes all ciphers
        AES = aes.AES()
        AES.add_to_private_key("key", keys["AES"])

        Paillier = paillier.Paillier()
        Paillier.add_to_private_key("lambda", 117668535328987834733689137263689797298977817639429644060749368527644686726669296731885251952344689212879739921514739655067928530440046015056096688399083645657472888121212951216520851399887876525989934400216686895826326664246358568791172640501226072668741206059249533639801502947840932944016267812429948585960L)
        Paillier.add_to_public_key("n", 117668535328987834733689137263689797298977817639429644060749368527644686726669296731885251952344689212879739921514739655067928530440046015056096688399083667529605534667335757959902320130332095941714707811038322265779765008946794346684879884355233783223579740293554891297286661970157653473900579699481419234807L)
        Paillier.add_to_public_key("g", 117668535328987834733689137263689797298977817639429644060749368527644686726669296731885251952344689212879739921514739655067928530440046015056096688399083667529605534667335757959902320130332095941714707811038322265779765008946794346684879884355233783223579740293554891297286661970157653473900579699481419234808L)
        # Paillier.add_to_private_key("lambda",
        #                             keys["Paillier"]["priv"]["lambda"])
        # Paillier.add_to_public_key("n", keys["Paillier"]["pub"]["n"])
        # Paillier.add_to_public_key("g", keys["Paillier"]["pub"]["g"])

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

    # 
    # Encrypts a query
    # pt: plaintex
    # 
    def encrypt(self, pt, skip_index = False):
        global oreEncoder

        assert type(pt) == dict
        result = {}

        # 
        # Encrypts each key according to the map
        # 
        for attribute in pt:
            if type(attribute) == dict:
                result[attribute] = self.encrypt( pt[attribute], skip_index = skip_index )
            elif attribute == "_id":
                result[attribute] = pt[attribute]
                continue
            else:
                result[attribute] = {}
                for attribute_type in self.__mapped_attr:
                    if attribute_type == "index" and skip_index:
                        continue
                    cipher = self.ciphers[attribute_type]
                    if attribute in self.__mapped_attr[attribute_type]:
                        # Add the related ciphertext for attribute_type
                        result[attribute][attribute_type] = cipher.encrypt( pt[attribute])
        return result

    # Decrypts the return of a query
    def decrypt(self, ct):
        assert type(ct) == dict

        ciphers = self.ciphers

        result = {}

        #
        # Decrypts each key according to the map
        # 
        for attribute in ct:
            if type(attribute) == dict:
                result[attribute] = self.encrypt( ct[attribute], skip_index = skip_index )
            elif attribute == "_id":
                result[attribute] = ct[attribute]
                continue
            else:
                result[attribute] = {}
                for attribute_type in [x for x in self.__mapped_attr if x != "index"]:
                    # 
                    # There is no support for decryption of index attributes
                    # 
                    cipher = self.ciphers[attribute_type]
                    if attribute in self.__mapped_attr[attribute_type]:
                        # Add the related ciphertext for attribute_type
                        result[attribute][attribute_type] = cipher.decrypt( ct[attribute][attribute_type])
                        if is_int(result[attribute][attribute_type]):
                            result[attribute][attribute_type] = int(result[attribute][attribute_type])
        return result

    def get_ctL(self, target):
        # Returns the left side of the ciphertext
        cipher = self.ciphers["index"]
        return cipher.encrypt(target)[0]

    def get_ctR(self, target):
        # Returns the right side of the ciphertext
        cipher = self.ciphers["index"]
        return cipher.encrypt(target)[1]

    def get_supported_attr_types(self):
        return tuple(self.__supported_attr_types)

    # 
    # Maps an attribute to one of those supported fields
    # 
    def add_attr(self, name, attribute = "static"):
        assert type(name) == str
        assert type(attribute) == str
        assert attribute in self.__supported_attr_types

        if attribute not in self.__mapped_attr.keys():
            self.__mapped_attr[attribute] = [name]
        else:
            assert type(self.__mapped_attr[attribute]) == list
            self.__mapped_attr[attribute].append(name)