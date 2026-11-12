"""Keyed EDM hashing (`edm` format), byte-compatible with the Rust `edm-hash --format edm`."""
import base64
import binascii
import hashlib
import hmac
import itertools
import json
import logging
import os
import tempfile
import unicodedata
from datetime import datetime

from edmtool import errors
from edmtool.file_transformer import FileTransformer
from edmtool.hasher import Hasher

ALGO = "hmac-sha256"
HASHED_MAGIC = "#edm-hashed "
KEY_ENV = "EDM_KEY_HEX"
MIN_KEY_LEN = 32
ASCII_WS = b" \t\n\r\x0c"

PURVIEW_SEPS = frozenset(" \t,.;?!\r\n")
WB_SEPS = frozenset(Hasher.chars_to_split_on)

CLS_DIGIT, CLS_ALPHA, CLS_OTHER = 1, 2, 4
# Shape-set limits of the Rust `shape` module.
MAX_N, MAX_LEN, MAX_LONG, PREFIX_K = 16, 255, 1 << 16, 4


class View:
    """Per-column tokenisation: separator set, case folding, ignored delimiters."""

    def __init__(self, seps, lowercase=True, ignored=""):
        self.seps = seps
        self.lowercase = lowercase
        self.ignored = "".join(sorted(set(ignored)))
        self._sep_set = PURVIEW_SEPS if seps == "purview" else WB_SEPS
        self._ignored_set = frozenset(self.ignored)

    def key(self):
        return (self.seps, self.lowercase, self.ignored)

    def desc(self):
        return {"seps": self.seps, "lowercase": self.lowercase, "ignored": self.ignored}


def purview_view(lowercase=True, ignored=""):
    return View("purview", lowercase, ignored)


def wb_view():
    return View("wb", True, "")


def parse_purview_col(spec: str):
    """NAME[:case][:ignored=CHARS] -> (name, View); CHARS runs to the end, so it may hold ':'."""
    name, _, ignored = spec.partition(":ignored=")
    lowercase = not name.endswith(":case")
    if not lowercase:
        name = name[:-len(":case")]
    if not name:
        raise errors.MissingArgumentsError(f"bad --purview-col {spec!r}")
    return name, purview_view(lowercase, ignored)


def simple_lower(c: str) -> str:
    """Per-code-point simple lowercase (no final sigma, U+0130 -> 'i'), as in the Rust engine."""
    if c == "İ":
        return "i"
    lc = c.lower()
    return lc if len(lc) == 1 else c


def char_class(c: str) -> int:
    if "0" <= c <= "9":
        return CLS_DIGIT
    if "a" <= c <= "z" or "A" <= c <= "Z":
        return CLS_ALPHA
    return CLS_OTHER


def tokenize(value: str, view: View, lower: str):
    """Returns [(token, class bits)] of a cell."""
    s = unicodedata.normalize("NFKC", value)
    fold = view.lowercase
    if lower == "python" and fold:
        # edm-cli order: NFKC, str.lower on the whole cell, then split.
        s, fold = s.lower(), False
    toks, cur, cls = [], [], 0
    for c in s:
        if c in view._sep_set:
            if cur:
                toks.append(("".join(cur), cls))
                cur, cls = [], 0
            continue
        if fold:
            c = simple_lower(c)
        if c in view._ignored_set:
            continue
        cur.append(c)
        cls |= char_class(c)
    if cur:
        toks.append(("".join(cur), cls))
    return toks


class ShapeSet:
    """Primary-shape metadata the Rust index uses to gate n-gram hashing."""

    def __init__(self):
        self.dense = set()
        self.long = {}
        self.long_known = True
        self.prefix = set()

    def insert(self, toks):
        n = len(toks)
        cls = 0
        for _, c in toks:
            cls |= c
        length = sum(len(t) for t, _ in toks) + n - 1
        if n <= MAX_N:
            self.dense.add((n, cls, min(length, MAX_LEN)))
        elif self.long_known:
            k = (n, length)
            if len(self.long) >= MAX_LONG and k not in self.long:
                self.long_known = False
                self.long.clear()
            else:
                self.long[k] = self.long.get(k, 0) | (1 << cls)
        pcls, plen = 0, -1
        for k in range(1, min(n, PREFIX_K + 1)):
            t, c = toks[k - 1]
            pcls |= c
            plen += len(t) + 1
            self.prefix.add((k, pcls, min(plen, MAX_LEN)))

    def shapes(self):
        v = [list(s) for s in sorted(self.dense)]
        if self.long_known:
            for (n, length), m in sorted(self.long.items()):
                v.extend([n, c, length] for c in range(8) if m & (1 << c))
        return v

    def prefixes(self):
        return [list(s) for s in sorted(self.prefix)]


def key_id(key: bytes) -> str:
    return hashlib.sha256(b"edm-key-id" + key).digest()[:8].hex()


def validate_key(key: bytes) -> bytes:
    if len(key) < MIN_KEY_LEN:
        raise errors.InvalidKeyError(f"EDM key must be at least {MIN_KEY_LEN} bytes")
    return key


def load_key(key_file=None) -> bytes:
    """Hex key from `key_file`, else from $EDM_KEY_HEX (same sources as Rust edm-hash)."""
    if key_file:
        with open(key_file, "rb") as f:
            h, src = f.read(), key_file
    else:
        h, src = os.environ.get(KEY_ENV), f"${KEY_ENV}"
        if h is None:
            raise errors.MissingArgumentsError(f"{ALGO} needs --key-file or ${KEY_ENV}")
        h = h.encode()
    try:
        # Same whitespace as Rust trim_ascii; non-hex bytes fail in unhexlify.
        return validate_key(binascii.unhexlify(h.strip(ASCII_WS)))
    except binascii.Error as e:
        raise errors.InvalidKeyError(f"EDM key in {src} is not valid hex: {e}")


class KeyedHasher:

    def __init__(self, key: bytes):
        self._mac = hmac.new(key, digestmod=hashlib.sha256)
        self.key_id = key_id(key)

    def fp(self, data: bytes) -> bytes:
        m = self._mac.copy()
        m.update(data)
        return m.digest()[:8]


class KeyedOptions:

    def __init__(self,
                 key: bytes,
                 tokenizer="purview",
                 lower="simple",
                 purview_cols=(),
                 shapes=True,
                 delimiter=",",
                 allow_empty_cells=False):
        if tokenizer not in ("purview", "wb"):
            raise errors.MissingArgumentsError(f"unknown --tokenizer {tokenizer}")
        if lower not in ("simple", "python"):
            raise errors.MissingArgumentsError("--lower must be python or simple")
        self.hasher = KeyedHasher(key)
        self.default_view = purview_view() if tokenizer == "purview" else wb_view()
        self.lower = lower
        self.views = [parse_purview_col(s) for s in purview_cols]
        self.shapes = shapes
        self.delimiter = delimiter
        self.allow_empty_cells = allow_empty_cells


def _strip_nl(b: bytes) -> bytes:
    """Strips the whole line terminator: a leftover '\r' would defeat the empty-cell check."""
    return b.rstrip(b"\r\n")


def hash_table(src_path: str, dst_path: str, o: KeyedOptions):
    """Writes the `edm` hashed CSV; returns (meta, rows, skipped, sha256 hex, size)."""
    with open(src_path, "rb") as src:
        first = src.readline()
        if not first:
            raise errors.MissingArgumentsError("empty input")
        header = first.decode("utf-8").rstrip("\r\n")
        if header.startswith("\ufeff"):
            header = header[1:]
        names = header.split(o.delimiter)
        if any("," in n for n in names):
            raise errors.MissingArgumentsError("column names must not contain ','")
        for n, _ in o.views:
            if n not in names:
                raise errors.MissingArgumentsError(f"view for unknown column {n!r}")

        views, col_views = [], []
        for n in names:
            v = next((v for c, v in o.views if c == n), o.default_view)
            i = next((i for i, x in enumerate(views) if x.key() == v.key()), None)
            if i is None:
                views.append(v)
                i = len(views) - 1
            col_views.append(i)

        ncols = len(names)
        shapes = [ShapeSet() for _ in range(ncols)]
        rows, skipped, unknown = 0, 0, 0
        out_dir = os.path.dirname(os.path.abspath(dst_path))
        with tempfile.TemporaryFile(mode="w+b", dir=out_dir) as tmp:
            for lineno, raw in enumerate(src, start=2):
                line = _strip_nl(raw).decode("utf-8")
                if not line:
                    skipped += 1
                    continue
                cells = line.split(o.delimiter)
                if len(cells) != ncols:
                    skipped += 1
                    logging.info(f"Row {lineno} has {len(cells)} cells, expected {ncols}; skipped")
                    continue
                out = []
                for i, c in enumerate(cells):
                    if c == "" and not o.allow_empty_cells:
                        out = None
                        break
                    if not c.isascii() and any(unicodedata.category(x) == "Cn" for x in c):
                        unknown += 1
                    toks = tokenize(c, views[col_views[i]], o.lower)
                    joined = " ".join(t for t, _ in toks).encode("utf-8")
                    fp = o.hasher.fp(joined)
                    out.append(f"{len(toks)}|{base64.b64encode(fp).decode()}")
                    # Like edm-hash, cells before an empty one still add shapes (a harmless superset).
                    if o.shapes and toks:
                        shapes[i].insert(toks)
                if out is None:
                    skipped += 1
                    logging.info(f"Row {lineno} has an empty cell; skipped. "
                                 "Use --allow_empty_cells to include it.")
                    continue
                if rows:
                    tmp.write(b"\n")
                tmp.write(",".join(out).encode("utf-8"))
                rows += 1
            tmp.write(b"\n")
            if unknown:
                logging.warning(f"{unknown} cells contain code points unassigned in Unicode "
                                f"{unicodedata.unidata_version} (this Python); they may not match. "
                                "Use a newer Python.")

            columns = []
            for i, n in enumerate(names):
                col = {"name": n, "view": col_views[i]}
                if o.shapes:
                    col["shapes"] = shapes[i].shapes()
                    if shapes[i].long_known:
                        col["long_shapes"] = True
                    col["prefixes"] = shapes[i].prefixes()
                columns.append(col)
            meta = {
                "format": "edm",
                "version": 1,
                "algo": ALGO,
                "key_id": o.hasher.key_id,
                "lower": o.lower,
                "views": [v.desc() for v in views],
                "columns": columns,
                "rows": rows,
            }
            js = json.dumps(meta, ensure_ascii=False, separators=(",", ":"))
            tmp.seek(0)
            sha, size = hashlib.sha256(), 0
            with open(dst_path, "wb") as dst:
                head = f"{HASHED_MAGIC}{js}\n{','.join(names)}\n".encode("utf-8")
                for chunk in itertools.chain([head], iter(lambda: tmp.read(1 << 20), b"")):
                    dst.write(chunk)
                    sha.update(chunk)
                    size += len(chunk)
    return meta, rows, skipped, sha.hexdigest(), size


class KeyedFileTransformer(FileTransformer):
    """`encode` for hmac-sha256: same output paths and metadata file as FileTransformer."""

    def __init__(self, opts: KeyedOptions):
        super().__init__(None, opts.delimiter, opts.allow_empty_cells)
        self._opts = opts

    def create_encoded_file(self, file_path: str):
        encoded_path = self._create_new_file_encoded(file_path)
        if self.check_file_exists(encoded_path):
            raise errors.EncodedFileExistsError(
                f"Encoded file exists under path {encoded_path}, please remove it first to proceed."
            )
        try:
            meta, rows, skipped, checksum, size = hash_table(file_path, encoded_path, self._opts)
        except Exception:
            if os.path.exists(encoded_path):
                os.remove(encoded_path)
            raise
        if skipped:
            logging.info(f"{skipped} rows were skipped")

        metadata = {
            'filename': os.path.basename(encoded_path),
            'checksum': checksum,
            'size': size,
            'algo': ALGO,
            'format': 'edm',
            'key_id': meta['key_id'],
            'date_created': datetime.now().isoformat(),
            'fields': [c['name'] for c in meta['columns']],
            'rows': rows,
        }
        with open(self._create_new_file_metadata(encoded_path), 'w') as f:
            json.dump(metadata, f)
        return checksum, size
