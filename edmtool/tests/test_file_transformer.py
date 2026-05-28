import json
import os
import tempfile
import unittest

from edmtool.hasher import Hasher
from edmtool.file_transformer import FileTransformer


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


class TestFileTransformerEmptyCells(unittest.TestCase):

    def _create_csv(self, content):
        f = tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False)
        f.write(content)
        f.close()
        return f.name

    def _read_encoded(self, csv_path):
        encoded_path = csv_path.replace('.csv', '_encoded.csv')
        metadata_path = encoded_path.replace('.csv', '_metadata.json')
        with open(encoded_path) as f:
            lines = f.read().strip().split('\n')
        with open(metadata_path) as f:
            metadata = json.load(f)
        return lines, metadata, encoded_path, metadata_path

    def _cleanup(self, *paths):
        for p in paths:
            if os.path.exists(p):
                os.unlink(p)

    def test_empty_cells_skipped_by_default(self):
        csv_path = self._create_csv(
            "name,email,zip\n"
            "Jane,,10002\n"
            "Alice,alice@acme.com,90210\n"
        )
        ft = FileTransformer(Hasher('sha256'))
        ft.create_encoded_file(csv_path)
        lines, metadata, enc, meta = self._read_encoded(csv_path)

        data_rows = lines[1:]
        self.assertEqual(len(data_rows), 1, "Row with empty cell should be skipped")
        self._cleanup(csv_path, enc, meta)

    def test_empty_cells_allowed_with_flag_sha256(self):
        csv_path = self._create_csv(
            "name,email,zip\n"
            "Jane,,10002\n"
            "Alice,alice@acme.com,90210\n"
        )
        ft = FileTransformer(Hasher('sha256'), allow_empty_cells=True)
        ft.create_encoded_file(csv_path)
        lines, metadata, enc, meta = self._read_encoded(csv_path)

        data_rows = lines[1:]
        self.assertEqual(len(data_rows), 2, "All rows should be kept with allow_empty_cells")

        empty_cell_hash = "0|47DEQpj8HBSa+/TImW+5JCeuQeRkm5NMpJWZG3hSuFU="
        cells = data_rows[0].split(',')
        self.assertEqual(cells[1], empty_cell_hash)
        self._cleanup(csv_path, enc, meta)

    def test_empty_cells_allowed_with_flag_spooky(self):
        csv_path = self._create_csv(
            "name,email,zip\n"
            "Jane,,10002\n"
            "Alice,alice@acme.com,90210\n"
        )
        ft = FileTransformer(Hasher('spooky'), allow_empty_cells=True)
        ft.create_encoded_file(csv_path)
        lines, metadata, enc, meta = self._read_encoded(csv_path)

        data_rows = lines[1:]
        self.assertEqual(len(data_rows), 2)

        empty_cell_hash = "0|UfIPiOZtXZU="
        cells = data_rows[0].split(',')
        self.assertEqual(cells[1], empty_cell_hash)
        self._cleanup(csv_path, enc, meta)

    def test_all_cells_empty_in_row(self):
        csv_path = self._create_csv(
            "name,email\n"
            ",\n"
            "Alice,alice@acme.com\n"
        )
        ft = FileTransformer(Hasher('sha256'), allow_empty_cells=True)
        ft.create_encoded_file(csv_path)
        lines, metadata, enc, meta = self._read_encoded(csv_path)

        data_rows = lines[1:]
        self.assertEqual(len(data_rows), 2)

        empty_cell_hash = "0|47DEQpj8HBSa+/TImW+5JCeuQeRkm5NMpJWZG3hSuFU="
        cells = data_rows[0].split(',')
        self.assertTrue(all(c == empty_cell_hash for c in cells))
        self._cleanup(csv_path, enc, meta)

    def test_no_empty_cells_unaffected_by_flag(self):
        csv_path = self._create_csv(
            "name,email\n"
            "Jane,jane@acme.com\n"
            "Alice,alice@acme.com\n"
        )
        ft_default = FileTransformer(Hasher('sha256'))
        ft_default.create_encoded_file(csv_path)
        lines_default, _, enc, meta = self._read_encoded(csv_path)
        self._cleanup(enc, meta)
        os.unlink(csv_path)

        csv_path = self._create_csv(
            "name,email\n"
            "Jane,jane@acme.com\n"
            "Alice,alice@acme.com\n"
        )
        ft_flag = FileTransformer(Hasher('sha256'), allow_empty_cells=True)
        ft_flag.create_encoded_file(csv_path)
        lines_flag, _, enc, meta = self._read_encoded(csv_path)

        self.assertEqual(lines_default, lines_flag, "Flag should not affect CSVs without empty cells")
        self._cleanup(csv_path, enc, meta)


if __name__ == '__main__':
    unittest.main()
