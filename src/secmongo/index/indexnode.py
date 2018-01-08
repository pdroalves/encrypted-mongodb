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
from .node import Node


class IndexNode(Node):
    value = None
    _id = []

    def __init__(self, value, _id=[]):
        self.value = value
        self._id = _id if _id in (list, tuple) else [_id]

    def compare(self, other, **kwargs):
        if type(other) in (list, tuple):
            x = other[0]
        else:
            x = other
        # Compares x with self
        if x == self.value:
            return 0
        elif x < self.value:
            return -1
        elif x > self.value:
            return 1
