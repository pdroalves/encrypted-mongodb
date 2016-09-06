"""Permutation tests."""
import unittest


RUNS = 256


class PermutationTest(unittest.TestCase):
    """Permutation tests."""

    def setUp(self):
        """Set up a permutation instance."""
        import intperm
        self.perm = intperm.Permutation(seed=42)

    def test_map_to(self):
        """Test the map_to method."""
        self.assertEqual(self.perm.map_to(42), 4627128764160949907)

    def test_map_to_not_self(self):
        """Test the map_to method."""
        for i in range(RUNS):
            self.assertNotEqual(self.perm.map_to(i), i)

    def test_map_from(self):
        """Test the map_from method."""
        self.assertEqual(self.perm.map_from(4627128764160949907), 42)

    def test_map_from_reverse(self):
        """Test the map_from method."""
        for i in range(RUNS):
            self.assertEqual(self.perm.map_from(self.perm.map_to(i)), i)

    def test_map_from_reverse_random(self):
        """Test the map_from method with a random permutation."""
        import intperm
        perm = intperm.Permutation()
        for i in range(RUNS):
            self.assertEqual(perm.map_from(perm.map_to(i)), i)


class Permutation8bitTest(unittest.TestCase):
    """8-bit permutation tests."""

    def setUp(self):
        """Set up an 8-bit permutation instance."""
        import intperm
        self.perm = intperm.Permutation(8, seed=42)

    def test_map_to(self):
        """Test the map_to method."""
        self.assertEqual(self.perm.map_to(42), 191)

    def test_map_to_not_self(self):
        """Test the map_to method."""
        for i in range(RUNS):
            self.assertNotEqual(self.perm.map_to(i), i)

    def test_map_from(self):
        """Test the map_from method."""
        self.assertEqual(self.perm.map_from(191), 42)

    def test_map_from_reverse(self):
        """Test the map_from method."""
        for i in range(RUNS):
            self.assertEqual(self.perm.map_from(self.perm.map_to(i)), i)
