import unicodedata
import hashlib
import base64
import spookyhash
import re


class Hasher:

    def __init__(self, algo, seed=131313):
        if algo == "spooky":
            self.algo = "spooky"
            self._hashFn = self._spooky
            self._seed = seed
        else:
            self.algo = "sha256"
            self._hashFn = self._sha256

    def _spooky(self, data: bytes):
        return spookyhash.Hash64(data, self._seed).digest()

    def _sha256(self, data: bytes):
        return hashlib.sha256(data).digest()

    def _normalize(self, data: str):
        return unicodedata.normalize('NFKC', data)

    def _work_corner_cases(self, data: str):
        cleaned_data = re.sub(r"[^\w ́]+|(\s{2,})|_", " ", data.lower())
        return cleaned_data.strip()

    def _prepare_words(self, data: str):
        corner_cased_data = self._work_corner_cases(data)
        words = corner_cased_data.split()

        length = 0
        for word in words:
            length = length + 1
            dash_ap_count = word.count(' ́')
            if dash_ap_count > 0:
                length = length + dash_ap_count

        return length, corner_cased_data

    def _transform_into_base64(self, data: bytes):
        return base64.b64encode(data).decode()

    def encode(self, data: str):
        norm = self._normalize(data)
        len, prepared_str = self._prepare_words(norm)
        hashed = self._hashFn(prepared_str.encode('utf-32-le'))
        return str(len) + "|" + self._transform_into_base64(hashed)
