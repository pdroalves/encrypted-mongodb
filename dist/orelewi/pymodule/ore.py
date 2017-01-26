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

import LewiWuOREBlkLF as ore

# Bit length of plaintext space
n = 32
# Block size
k = 8

sk = ore.keygen(n, k)
ctA = ore.encrypt(2, sk, n, k)
ctB = ore.encrypt(1, sk, n, k)
ctC = ore.encrypt(3, sk, n, k)

assert ore.compare(n, k, ctA[0], ctA[1]) == 0
assert ore.compare(n, k, ctA[0], ctB[1]) == 1
assert ore.compare(n, k, ctA[0], ctC[1]) == -1
