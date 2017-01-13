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
class Cipher:

    def __init__(self,keys=None):
        self.keys = keys
        return

    def encrypt(self,x):
        return x

    def decrypt(self,c):
        return c

    @staticmethod
    def keygen(key_size):
        return None

    def has_keys(self):
        return True if self.keys and self.keys.has_key("pub") and self.keys.has_key("priv") else False

    def get_public_key(self):
        if self.keys is None:
            raise Exception("There is no keys!")
        if not self.keys.has_key("pub"):
            raise Exception("There is no public key!")
        
        return self.keys["pub"]

    def get_private_key(self):
        if self.keys is None:
            raise Exception("There is no keys!")        
        if not self.keys.has_key("priv"):
            raise Exception("There is no private key!")

        return self.keys["priv"]

    def add_to_public_key(self,name,value):
        if self.keys is None:
            self.keys = {}
        if not self.keys.has_key("pub"):
            self.keys["pub"] = {}

        self.keys["pub"][name] = value

    def add_to_private_key(self,name,value):
        if self.keys is None:
            self.keys = {}
        if not self.keys.has_key("priv"):
            self.keys["priv"] = {}

        self.keys["priv"][name] = value