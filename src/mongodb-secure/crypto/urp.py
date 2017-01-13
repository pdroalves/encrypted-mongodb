#!/usr/bin/python
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

class URP:
	def __init__(self,nbits=32, state=None,seed=42):
		self.nbits = nbits
		if state is None:
			random.seed(seed)
			self.rndstate = random.getstate()
		else:
			random.setstate(state)

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
		if x == 0:
			return 0
		assert type(x) in (int,long)

		# Backup state
		currently_state = random.getstate()

		# Input value
		bits = [int(i) for i in bin(x).partition("b")[2]]
		bits = [0]*(self.nbits-len(bits)) + bits
		p_bits = [None]*self.nbits

		# New indexes
		new_indexes = [None]*self.nbits

		# This guarantee we will build a new index map with unique values and 
		# different from the original map
		while 1 == 1:
			for i in range(self.nbits):
				new_index = random.randint(0,self.nbits-1)
				while new_index in new_indexes:
					new_index = random.randint(0,self.nbits-1)
				new_indexes[i] = new_index
			if new_indexes != bits:
				break
			else:
				new_indexes = [None]*self.nbits

		# Permutation
		for i,v in enumerate(bits):
			p_bits[new_indexes[i]] = v

		# return int("0b"+"".join([str(i) for i in p_bits]),2), currently_state
		return p_bits, currently_state

	def map_from(self,y):
		if y == 0:
			return 0
		# Backup state
		currently_state = self.get_state()

		if type(y) in (list,tuple) and type(y[0]) in (list,tuple) and type(y[1]) in (list,tuple):
			x = y[0]
			state = y[1]
		elif type(y) in (list,tuple):
			x = y
			state = self.get_state()
		else:
			assert type(y) in (int,long)
			x = [int(i) for i in bin(y).partition("b")[2]]
			state = self.get_state()

		# Set old state
		self.set_state(state)

		# input value
		bits = x
		bits = [0]*(self.nbits-len(bits)) + bits
		inv_p_bits = [None]*self.nbits
		
		# Index map
		new_indexes = [None]*self.nbits
		while 1 == 1:
			for i in range(self.nbits):
				new_index = random.randint(0,self.nbits-1)
				while new_index in new_indexes:
					new_index = random.randint(0,self.nbits-1)
				new_indexes[i] = new_index
			if new_indexes != bits:
				break
			else:
				new_indexes = [None]*self.nbits
		for i in range(self.nbits):
			inv_p_bits[i] = bits[new_indexes[i]]
		# Restore state
		self.set_state(currently_state)
		return int("0b"+"".join([str(i) for i in inv_p_bits]),2)

if __name__ == "__main__":

	urp = URP()
	for i in range(1,16):
		print i
		y = urp.map_to(i)
		assert urp.map_from(y) == i

	print "Test passed!"
