# Mimics BERT basic tokenization

import sys
import unicodedata


# Following https://github.com/google-research/bert/blob/master/tokenization.py
_punct_chars = set([
    chr(i) for i in range(sys.maxunicode)
    if (unicodedata.category(chr(i)).startswith('P') or
        ((i >= 33 and i <= 47) or (i >= 58 and i <= 64) or
         (i >= 91 and i <= 96) or (i >= 123 and i <= 126)))
])

_cjk_chars = set([
    chr(i) for i in range(sys.maxunicode)
    if ((i >= 0x4E00 and i <= 0x9FFF) or
        (i >= 0x3400 and i <= 0x4DBF) or
        (i >= 0x20000 and i <= 0x2A6DF) or
        (i >= 0x2A700 and i <= 0x2B73F) or
        (i >= 0x2B740 and i <= 0x2B81F) or
        (i >= 0x2B820 and i <= 0x2CEAF) or
        (i >= 0xF900 and i <= 0xFAFF) or
        (i >= 0x2F800 and i <= 0x2FA1F))
])

_strip_chars = set([
    chr(i) for i in range(sys.maxunicode)
    if i == 0 or i == 0xfffd or (
            chr(i) not in '\t\n\r' and unicodedata.category(chr(i)) in ('Cc', 'Cf')
    )
])


def _mapto(char):
    if char in _punct_chars or char in _cjk_chars:
        # Add space around punctuation and CJK chars for string.split()
        return ' ' + char + ' '
    elif char in _strip_chars:
        return None
    else:
        raise ValueError(char)


_translation_table = str.maketrans({
    c: _mapto(c) for c in _punct_chars | _cjk_chars | _strip_chars
})


def basic_tokenize(text):
    return text.translate(_translation_table).split()
