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
from Crypto import Random
import random

class URPINT:
	def __init__(self,n=16, state=None,seed=42):
		self.n = n
		if state is None:
			random.seed(seed)
			self.rndstate = random.getstate()
		else:
			random.setstate(state)

		self.perm_indexes = [None]*n
		self.inv_perm_indexes = [None]*n
		original_indexes = range(n)
		# This guarantee we will build a new index map with unique values and 
		# different from the original map
		while 1 == 1:
			for i in range(self.n):
				new_index = random.randint(0,self.n-1)
				while new_index in self.perm_indexes:
					new_index = random.randint(0,self.n-1)
				self.perm_indexes[i] = new_index
			if self.perm_indexes != original_indexes:
				break
			else:
				perm_indexes = [None]*self.n

		# Build the inverse map
		for i,v in enumerate(self.perm_indexes):
			self.inv_perm_indexes[v] = i

	def get_int(self,start,end):
		return random.randint(start,end)

	def get_initial_state(self):
		return self.rndstate
	
	def get_state(self):
		return random.getstate()
	
	def set_state(self,state):
		random.setstate(state)

	def refresh(self):
		self.set_state(self.get_initial_state())

	def map_to(self,x):
		return self.perm_indexes[x]

	def map_from(self,y):
		return self.inv_perm_indexes[y]

if __name__ == "__main__":

	urp = URPINT()
	for i in range(1,16):
		print i
		y = urp.map_to(i)
		assert urp.map_from(y) == i

	print "Test passed!"
