#!/usr/bin/python
import LewiWuOREBlk as ore
import LewiWuOREBlkLF as oreLF
from random import randint
import unittest
import sys
from math import log

class TestOREBlk(unittest.TestCase):
	N = 100

	def setUp(self):
		self.sk = ore.keygen(32,8)

	def test_several_comparisons(self):
		for _ in range(self.N):
			pt1 = randint(0,pow(2,32));
			pt2 = randint(0,pow(2,32));
			ct1 = ore.encrypt(pt1,self.sk,32,8)
			ct2 = ore.encrypt(pt2,self.sk,32,8)

			r = ore.compare(32,8,ct1[0],ct1[1],ct2[0],ct2[1])
			r_expected = (1 if pt1 > pt2 else (-1 if pt1 < pt2 else 0))
			if r != r_expected:
				print "Fail! - pt1:\t%d,\tpt2:\t%d\texpected\t%d,\treceived %d\tdiff:\t%d\tdiffbits:\t%d" % (pt1,pt2,r_expected,r,pt1-pt2,log(pt1,2))
				self.assertEqual(r, r_expected)

class TestOREBlkLF(unittest.TestCase):
	N = 100
	def setUp(self):
		self.sk = oreLF.keygen(32,8)

	def test_several_comparisons_lf(self):
		for _ in range(self.N):
			pt1 = randint(0,pow(2,32));
			pt2 = randint(0,pow(2,32));
			ct1 = oreLF.encrypt(pt1,self.sk,32,8)
			ct2 = oreLF.encrypt(pt2,self.sk,32,8)

			r = oreLF.compare(32,8,ct1[0],ct2[1])
			r_expected = (1 if pt1 > pt2 else (-1 if pt1 < pt2 else 0))
			if r != r_expected:
				print "Fail! - pt1:\t%d,\tpt2:\t%d\texpected\t%d,\treceived %d\tdiff:\t%d\tdiffbits:\t%d" % (pt1,pt2,r_expected,r,pt1-pt2,log(pt1,2))
				self.assertEqual(r, r_expected)

if __name__ == '__main__':
	# if len(sys.argv) > 1:
		# TestOREBlk.N = (int)(sys.argv.pop())
		# TestOREBlkLF.N = TestOREBlk.N

	print "Running for %d comparisons" % TestOREBlk.N
	unittest.main()