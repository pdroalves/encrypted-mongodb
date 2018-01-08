import LewiWuOREBlkLF as ore
import random

class ORE():
    n = None  # Bit length of plaintext space
    k = None  # Block size (in bits)

    def __init__(self):
        pass

    # message space size N > 0
    # d-ary strings x = x_1x_2x_3...x_n
    def keygen(self, n=32, k=8):
        self.n = n
        self.k = k

        self.sk = ore.keygen(n, k)
        return self

    def encrypt(self, y):
        if type(y) == str:
            y = int(y)
        return ore.encrypt(y, self.sk, self.n, self.k)

    @staticmethod
    def compare(ctL, ctR, n=32, k=8):
        return ore.compare(n, k, ctL, ctR)

if __name__ == '__main__':
    orelf = ORE()
    sk = orelf.keygen()
    ctA = orelf.encrypt(2)
    ctB = orelf.encrypt(1)
    ctC = orelf.encrypt(3)

    print ctA

    assert ORE.compare(ctA[0], ctA[1]) == 0
    assert ORE.compare(ctA[0], ctB[1]) == 1
    assert ORE.compare(ctA[0], ctC[1]) == -1
