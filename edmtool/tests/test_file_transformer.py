import unittest
from edmtool.hasher import Hasher


class TestHasher(unittest.TestCase):

    def test_sha256(self):
        h = Hasher('sha256')
        self.assertEqual(h.encode("Mary Jones"), "2|Av4c8KiE0Eee3L3GCnZwnIRJibYlpcGXgz3XHc6zM8A=")

    def test_spooky_two_words(self):
        h = Hasher('spooky', 131313)
        self.assertEqual(h.encode("Mary Jones"), "2|IpyT7w5Qb0w=")

    def test_spooky_three_words_with_apostrophe(self):
        h = Hasher('spooky', 131313)
        self.assertEqual(h.encode("Mary s Jones"), "3|SAv8Lk0a4o8=")

    def test_spooky_three_words_with_accent(self):
        h = Hasher('spooky', 131313)
        self.assertEqual(h.encode("Mary´s Jones"), "3|vvtu63b9GoE=")

    def test_spooky_with_multiple_accents(self):
        h = Hasher('spooky', 131313)
        self.assertEqual(h.encode("M´ary´s Jones"), "4|I22VXv3/7kY=")

    def test_spooky_with_multiple_apostrophes(self):
        h = Hasher('spooky', 131313)
        self.assertEqual(h.encode("M'ary's Jones"), "4|9G/d0UUi2lI=")


if __name__ == '__main__':
    unittest.main()
