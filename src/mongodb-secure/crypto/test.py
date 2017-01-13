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
# import sys
# sys.setrecursionlimit(100000)
from index.binarytree import BinaryTree
from index.simplenode import SimpleNode
from index.encryptednode import EncryptedNode
from random import randint,shuffle
from crypto.ore import ORESMALL as ORE
N = 1000
elements = range(1,N)
shuffle(elements)
root = BinaryTree(elements[0])

print "Insertion..."
for i,e in enumerate(elements[1:]):
    # %timeit root.insert(e)
    root = root.insert(e)
print "The tree has %d elements and is %s" % (root.count_nodes(), "balanced" if root.is_balanced() else "not balanced")
print "Searching..."
for i in elements[1:]:
    # print i
    assert root.find(i)
print "It passed!"
%timeit root.find(30)

print "Time to test encryption..."
elements = range(1,N)
# shuffle(elements)
ore = ORE()
ore.keygen("oi",N)
print "keygen ok"
root.encrypt(ore)
print "The tree is encrypted"

print "Searching..."
root.find(ore.encrypt(99))
print "Done"


see = lambda x: "%s => %s %s" % (x.me.value, x.left.me.value if x.left else None, x.right.me.value if x.right else None)
# (self.me.value, self.left.me.value if self.left else None, self.right.me.value if self.right else None)