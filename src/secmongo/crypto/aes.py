#!/usr/bin/env python
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
import base64
from .cipher import Cipher
from Crypto import Cipher as CryptoCipher
from Crypto import Random
# from Crypto.Hash import SHA256
import hashlib
import base64

BS = 16


def pad(s):
    return s + (BS - len(s) % BS) * chr(BS - len(s) % BS)


def unpad(s):
    return s[:-ord(s[len(s)-1:])]


class AES(Cipher):

    # Generates a key using a hash of some passphrase
    @staticmethod
    def keygen(passphrase, secure=128):
        return base64.b64encode(hashlib.sha256(passphrase).digest())

    def encrypt(self, raw):
        raw = pad(str(raw))
        iv = Random.new().read(CryptoCipher.AES.block_size)
        cipher = CryptoCipher.AES.new(base64.b64decode(self.get_private_key()['key']),
                                      CryptoCipher.AES.MODE_CBC,
                                      iv)
        return base64.b64encode(iv + cipher.encrypt(raw))

    def decrypt(self, enc):
        enc = base64.b64decode(enc)
        iv = enc[:16]
        cipher = CryptoCipher.AES.new(base64.b64decode(self.get_private_key()['key']),
                                      CryptoCipher.AES.MODE_CBC,
                                      iv)
        return unpad(cipher.decrypt(enc[16:]))
