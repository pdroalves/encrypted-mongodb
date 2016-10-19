#!/usr/bin/env python
#coding:utf-8
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

import LewiWuOREBlkLF as oreLF

class ORE():
    d = None
    n = None


    # Generates a key using a hash of some passphrase
    # message space size N > 0
    # d-ary strings x = x_1x_2x_3...x_n
    def keygen( self,d = 32, n = 8):
        self.d = d
        self.n = n

        self.sk = oreLF.keygen(d,n)
    	return self.sk

    def encrypt( self, y ):
        return  oreLF.encrypt(y,self.sk,self.d,self.n)

    @staticmethod
    def compare( ctL, ctR ):
        return oreLF.compare(32,8,ctL,ctR)
