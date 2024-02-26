import unittest
from edmtool.hasher import Hasher


class TestHasher(unittest.TestCase):

    examples = [
        "Malani-e",
        "Malani'e",
        "Malani`e",
        "Malani_e",
        "Malani´e",
        "Malani e",
        "Malanie`",
        "Malanie'",
        "Malanie_",
        "Malanie´",
        "Malanie ",
        "Malanie-",
    ]
    encoded_examples = [
        "2|Kt5JjRhFkmE=",
        "2|Kt5JjRhFkmE=",
        "2|Kt5JjRhFkmE=",
        "2|Kt5JjRhFkmE=",
        "2|yILM4iRjvOw=",
        "2|Kt5JjRhFkmE=",
        "1|hgGce4EZtUs=",
        "1|hgGce4EZtUs=",
        "1|hgGce4EZtUs=",
        "2|Ngzhonfkvyo=",
        "1|hgGce4EZtUs=",
        "1|hgGce4EZtUs=",
    ]

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

    def test_spooky_hash_battery(self):
        h = Hasher('spooky', 131313)
        for i, example in enumerate(self.examples):
            self.assertEqual(h.encode(example), self.encoded_examples[i])


if __name__ == '__main__':
    unittest.main()
