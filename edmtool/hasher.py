import unicodedata
import hashlib
import base64
import spookyhash


class Hasher:
    wb_list = [
        0x0000, 0x0001, 0x0002, 0x0003, 0x0004, 0x0005, 0x0006, 0x0007, 0x0008, 0x0009, 0x000A,
        0x000B, 0x000C, 0x000D, 0x000E, 0x000F, 0x0010, 0x0011, 0x0012, 0x0013, 0x0014, 0x0015,
        0x0016, 0x0017, 0x0018, 0x0019, 0x001A, 0x001B, 0x001C, 0x001D, 0x001E, 0x001F, 0x0020,
        0x0021, 0x0022, 0x0026, 0x0027, 0x0028, 0x0029, 0x002A, 0x002B, 0x002C, 0x002D, 0x002E,
        0x002F, 0x003A, 0x003B, 0x003C, 0x003D, 0x003E, 0x003F, 0x0040, 0x005B, 0x005C, 0x005D,
        0x005E, 0x005F, 0x0060, 0x007B, 0x007C, 0x007D, 0x007E, 0x007F, 0x0080, 0x0081, 0x0082,
        0x0084, 0x0085, 0x0086, 0x0087, 0x0088, 0x0089, 0x008B, 0x008C, 0x008D, 0x008F, 0x0090,
        0x0091, 0x0092, 0x0093, 0x0094, 0x0095, 0x0096, 0x0097, 0x0098, 0x0099, 0x009B, 0x009C,
        0x009D, 0x00A0, 0x00A1, 0x00A2, 0x00A3, 0x00A4, 0x00A5, 0x00A6, 0x00A7, 0x00A8, 0x00A9,
        0x00AA, 0x00AB, 0x00AC, 0x00AD, 0x00AE, 0x00AF, 0x00B0, 0x00B1, 0x00B2, 0x00B3, 0x00B4,
        0x00B5, 0x00B6, 0x00B7, 0x00B8, 0x00B9, 0x00BA, 0x00BB, 0x00BC, 0x00BD, 0x00BE, 0x00BF,
        0x00D7, 0x00F7, 0x058A, 0x05BE, 0x061C, 0x1400, 0x1680, 0x1806, 0x2000, 0x2001, 0x2002,
        0x2003, 0x2004, 0x2005, 0x2006, 0x2007, 0x2008, 0x2009, 0x200A, 0x200E, 0x200F, 0x2010,
        0x2011, 0x2012, 0x2013, 0x2014, 0x2015, 0x2018, 0x2019, 0x201B, 0x201C, 0x201D, 0x201F,
        0x2024, 0x2025, 0x2026, 0x2028, 0x2029, 0x202A, 0x202B, 0x202C, 0x202D, 0x202E, 0x202F,
        0x2039, 0x203A, 0x203F, 0x2040, 0x2054, 0x205F, 0x2E02, 0x2E03, 0x2E04, 0x2E05, 0x2E09,
        0x2E0A, 0x2E0C, 0x2E0D, 0x2E17, 0x2E1A, 0x2E1C, 0x2E1D, 0x2E20, 0x2E21, 0x2E3A, 0x2E3B,
        0x2E40, 0x3000, 0x301C, 0x3030, 0x30A0, 0xFE31, 0xFE32, 0xFE33, 0xFE34, 0xFE4D, 0xFE4E,
        0xFE4F, 0xFE58, 0xFE63, 0xFF0D, 0xFF3F
    ]
    chars_to_split_on = [chr(h) for h in wb_list]

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

    def _prepare_words(self, data: str):
        words = []
        current_word = ""

        for char in data:
            if char in self.chars_to_split_on:
                if current_word:
                    words.append(current_word)
                    current_word = ""
            else:
                current_word += char

        if current_word:
            words.append(current_word)

        return len(words), " ".join(words).strip()

    def _transform_into_base64(self, data: bytes):
        return base64.b64encode(data).decode()

    def encode(self, data: str):
        norm = self._normalize(data)
        len, prepared_data = self._prepare_words(norm.lower())
        hashed = self._hashFn(prepared_data.encode('utf-32-le'))
        return str(len) + "|" + self._transform_into_base64(hashed)
