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
from node import Node

class IndexNode(Node):
    value = None
    _id = []

    def __init__(self,value,_id):
        # super(SimpleNode,self).__init__(x)
        self.value = value
        self._id = self._id + (_id if _id in (list,tuple) else [_id])
        
    def compare(self,other):
        if type(other) in (list,tuple):
            x = other[0] # gambiarra
        else:
            x = other # gambiarra
        # Compares x with self
        # if super(SimpleNode,self).value == x:
        if self.value == x:
            return 0
        # elif super(SimpleNode,self).value < x:
        elif self.value < x:
            return 1
        # elif super(SimpleNode,self).value > x:
        elif self.value > x:
            return 2