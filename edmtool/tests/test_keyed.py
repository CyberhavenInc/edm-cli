import argparse
import json
import os
import shutil
import tempfile
import unittest
from unittest import mock

from edmtool import errors, keyed
from edmtool.command_dispatcher import CommandDispatcher
from edmtool.command_handler import CommandHandler
from edmtool.utils import Calculate_file_sha256_checksum

DATA = os.path.join(os.path.dirname(__file__), "data", "keyed")

# Vector file -> KeyedOptions kwargs; must mirror the edm-hash flags in data/keyed/gen.sh.
VECTORS = {
    "default.csv": {},
    "purview_cols.csv": {
        "purview_cols": ["id:ignored=-", "email:case", "name:case:ignored=-'"]
    },
    "wb_python.csv": {
        "tokenizer": "wb",
        "lower": "python"
    },
    "wb_simple.csv": {
        "tokenizer": "wb"
    },
    "empty_cells.csv": {
        "allow_empty_cells": True
    },
    "no_shapes.csv": {
        "allow_empty_cells": True,
        "shapes": False
    },
}

KEY_FILE = os.path.join(DATA, "key.hex")


def _key():
    return keyed.load_key(KEY_FILE)


class TestRustVectors(unittest.TestCase):
    """Output must be byte-identical to the Rust edm-hash (vectors from data/keyed/gen.sh)."""

    def test_vectors(self):
        with tempfile.TemporaryDirectory() as d:
            for name, kw in VECTORS.items():
                with self.subTest(vector=name):
                    out = os.path.join(d, name)
                    keyed.hash_table(os.path.join(DATA, "table.csv"), out,
                                     keyed.KeyedOptions(_key(), **kw))
                    with open(out, "rb") as a, open(os.path.join(DATA, name), "rb") as b:
                        self.assertEqual(a.read(), b.read())

    def test_header_meta(self):
        with open(os.path.join(DATA, "default.csv"), encoding="utf-8") as f:
            first = f.readline()
        meta = json.loads(first[len(keyed.HASHED_MAGIC):])
        self.assertEqual(meta["algo"], "hmac-sha256")
        self.assertEqual(meta["key_id"], keyed.key_id(_key()))
        self.assertNotIn(_key().hex(), first)


class TestPurviewCol(unittest.TestCase):

    def test_parse(self):
        cases = {
            "id": ("id", True, ""),
            "id:case": ("id", False, ""),
            "mac:ignored=:-": ("mac", True, "-:"),
            "time:utc:case:ignored=:": ("time:utc", False, ":"),
        }
        for spec, (name, lower, ignored) in cases.items():
            with self.subTest(spec=spec):
                n, v = keyed.parse_purview_col(spec)
                self.assertEqual((n, v.lowercase, v.ignored), (name, lower, ignored))
        for bad in ("", ":case", ":ignored=-"):
            with self.subTest(spec=bad), self.assertRaises(errors.MissingArgumentsError):
                keyed.parse_purview_col(bad)


class TestNormalisation(unittest.TestCase):

    def test_simple_lower(self):
        self.assertEqual(keyed.simple_lower("İ"), "i")
        self.assertEqual(keyed.simple_lower("Σ"), "σ")
        self.assertEqual(keyed.simple_lower("ẞ"), "ß")

    def test_tokens(self):
        v = keyed.purview_view()
        self.assertEqual([t for t, _ in keyed.tokenize("ΟΔΥΣΣΕΑΣ", v, "simple")], ["οδυσσεασ"])
        self.assertEqual([t for t, _ in keyed.tokenize("ΟΔΥΣΣΕΑΣ", v, "python")], ["οδυσσεας"])
        self.assertEqual([t for t, _ in keyed.tokenize("İSTANBUL", v, "simple")], ["istanbul"])
        self.assertEqual([t for t, _ in keyed.tokenize("ﬁle １２", v, "simple")], ["file", "12"])
        v = keyed.purview_view(ignored="-")
        self.assertEqual([t for t, _ in keyed.tokenize("Middle-Last Name", v, "simple")],
                         ["middlelast", "name"])


class TestLineEndings(unittest.TestCase):
    """A '\r' left in the last cell must not defeat the empty-cell check."""

    def _hash(self, data, **kw):
        with tempfile.TemporaryDirectory() as d:
            src, out = os.path.join(d, "in.csv"), os.path.join(d, "out.csv")
            with open(src, "wb") as f:
                f.write(data)
            _, rows, skipped, _, _ = keyed.hash_table(src, out, keyed.KeyedOptions(_key(), **kw))
            with open(out, "rb") as f:
                return f.read(), rows, skipped

    def test_crlf_matches_lf(self):
        lf = b"name,city\nAlice,NY\nBob,\n"
        crlf = b"name,city\r\nAlice,NY\r\nBob,\r\n"
        self.assertEqual(self._hash(lf), self._hash(crlf))
        self.assertEqual(self._hash(lf, allow_empty_cells=True),
                         self._hash(crlf, allow_empty_cells=True))

    def test_crlf_empty_last_cell_is_skipped(self):
        _, rows, skipped = self._hash(b"name,city\r\nAlice,NY\r\nBob,\r\n")
        self.assertEqual((rows, skipped), (1, 1))


class TestKey(unittest.TestCase):

    def _write(self, d, data):
        p = os.path.join(d, "k")
        with open(p, "wb") as f:
            f.write(data)
        return p

    def test_key_file_hex(self):
        with tempfile.TemporaryDirectory() as d:
            # A trailing 0x0a/0x0d key byte is fine; the file's own newline is trimmed.
            k = b"\x00" * 31 + b"\n"
            self.assertEqual(keyed.load_key(self._write(d, k.hex().encode() + b"\r\n")), k)

    def test_key_rejected(self):
        with tempfile.TemporaryDirectory() as d:
            for bad in (b"", b"\n", b"ab" * 31, b"zz" * 32, b"a" * 65, b"\xab" * 32):
                with self.subTest(key=bad):
                    with self.assertRaises(errors.InvalidKeyError):
                        keyed.load_key(self._write(d, bad))

    def test_key_env_hex(self):
        with mock.patch.dict(os.environ, {"EDM_KEY_HEX": " " + "ab" * 32 + "\n"}):
            self.assertEqual(keyed.load_key(None), b"\xab" * 32)
        for bad in ("zz", "ab" * 32 + "\u2013", "\u00a0" + "ab" * 32):
            with self.subTest(key=bad), mock.patch.dict(os.environ, {"EDM_KEY_HEX": bad}):
                with self.assertRaises(errors.InvalidKeyError):
                    keyed.load_key(None)

    def test_key_missing(self):
        with mock.patch.dict(os.environ, {}, clear=True):
            with self.assertRaises(errors.MissingArgumentsError):
                keyed.load_key(None)

    def test_key_id(self):
        self.assertEqual(keyed.key_id(_key()), "a0d429b92500ba17")


class TestEncodeCommand(unittest.TestCase):

    def test_encode_hmac(self):
        with tempfile.TemporaryDirectory() as d:
            src = os.path.join(d, "table.csv")
            shutil.copy(os.path.join(DATA, "table.csv"), src)
            args = argparse.Namespace(action="encode",
                                      algorithm="hmac-sha256",
                                      db_file_path=src,
                                      db_file_delimiter=",",
                                      allow_empty_cells=False,
                                      key_file=KEY_FILE,
                                      tokenizer=None,
                                      lower=None,
                                      purview_col=[],
                                      no_shapes=False)
            CommandHandler(mock.Mock()).encode(args)
            with open(os.path.join(d, "table_encoded.csv"), "rb") as a, \
                    open(os.path.join(DATA, "default.csv"), "rb") as b:
                self.assertEqual(a.read(), b.read())
            with open(os.path.join(d, "table_encoded_metadata.json")) as f:
                meta = json.load(f)
            self.assertEqual(meta["algo"], "hmac-sha256")
            self.assertEqual(meta["key_id"], "a0d429b92500ba17")
            self.assertEqual(meta["fields"], ["name", "city", "id", "email"])
            self.assertEqual(meta["rows"], 8)
            self.assertEqual(meta["filename"], "table_encoded.csv")
            enc = os.path.join(d, "table_encoded.csv")
            self.assertEqual(meta["checksum"], Calculate_file_sha256_checksum(enc))
            self.assertEqual(meta["size"], os.path.getsize(enc))

    def test_keyed_flags_need_hmac(self):
        for algo in ("sha256", "spooky"):
            args = argparse.Namespace(action="encode",
                                      algorithm=algo,
                                      db_file_path="unused.csv",
                                      db_file_delimiter=",",
                                      key_file=KEY_FILE,
                                      purview_col=[])
            with self.subTest(algo=algo), self.assertRaisesRegex(errors.MissingArgumentsError,
                                                                 "--key-file need"):
                CommandHandler(mock.Mock()).encode(args)


class TestCliAbbreviations(unittest.TestCase):
    """The keyed flags must not make abbreviations of older flags ambiguous."""

    def test_legacy_prefixes(self):
        p = CommandDispatcher().parser
        for flag, dest, v in (("--tok", "token", "t"), ("--alg", "algorithm", "sha256"),
                              ("--n", "name", "n")):
            with self.subTest(flag=flag):
                self.assertEqual(getattr(p.parse_args(["upload", flag, v]), dest), v)
        self.assertEqual(p.parse_args(["encode", "--algo", "hmac-sha256"]).algorithm, "hmac-sha256")


class TestUploadRejectsKeyed(unittest.TestCase):

    def test_reject(self):
        with tempfile.TemporaryDirectory() as d:
            p = os.path.join(d, "m.json")
            with open(p, "w") as f:
                json.dump({"algo": "hmac-sha256"}, f)
            client = mock.Mock()
            h = CommandHandler(client)
            for action in ("create", "update", "upload"):
                args = argparse.Namespace(action=action,
                                          id="db",
                                          name="n",
                                          description="d",
                                          metadata_file_path=p)
                with self.subTest(action=action), \
                        self.assertRaises(errors.UnsupportedAlgorithmError):
                    getattr(h, action)(args)
            self.assertFalse(client.method_calls)


if __name__ == "__main__":
    unittest.main()
