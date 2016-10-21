#!/usr/bin/python
import LewiWuOREBlk as ore
import LewiWuOREBlkLF as oreLF
import sys
from random import randint
from math import log
import pytest

d = 2
n = 8

pt1 = randint(0,pow(2,n));
pt2 = randint(0,pow(2,n));

sk = ore.keygen(d,n)
ct1 = ore.encrypt(pt1,sk,d,n)
ct2 = ore.encrypt(pt2,sk,d,n)

sklf = oreLF.keygen(d,n)
ct1lf = oreLF.encrypt(pt1,sk,d,n)
ct2lf = oreLF.encrypt(pt2,sk,d,n)

def encrypt_oreblk():
	ore.encrypt(pt1,sk,d,n)

def encrypt_oreblklf():
	oreLF.encrypt(pt1,sk,d,n)

def compare_oreblk():
	ore.compare(d,n,ct1[0],ct1[1],ct2[0],ct2[1])

def compare_oreblklf():
	oreLF.compare(d,n,ct1lf[0],ct2lf[1])

def test_ore_compare(benchmark):
	benchmark(compare_oreblk)
	
def test_ore_encrypt(benchmark):
	benchmark(encrypt_oreblk)

def test_orelf_encrypt(benchmark):
	benchmark(encrypt_oreblklf)

def test_orelf_compare(benchmark):
	benchmark(compare_oreblklf)
