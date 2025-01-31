import pathlib
import re
from itertools import zip_longest, chain, accumulate
from typing import Literal, Iterable

from ._lib import load_dictionary, hyphenate_words_numbers, hyphenate_words_simple

whitespace_pattern = re.compile(r'\s+')

def clean_whitespace(text: str) -> str:
    """Hyphenation is only defined for words. This function breaks the text into words seperated by newline characters."""
    return whitespace_pattern.sub('\n', text)

def to_spans(int_output: list[int], skip_whitespace: bool=True) -> list[tuple[int, int]]:
    acc = chain((0,), accumulate(map(abs, int_output)))
    return [
        (a, a + abs(l)) for a, l in zip(acc, int_output) if not skip_whitespace or l > 0
    ]


class Hyphenator:
    def __init__(
        self,
        dictpath: str = "/usr/share/hyphen/hyph_en_US.dic",
        mode: Literal["raw", "str", "int", "spans"] = "str",
    ):
        assert mode in (
            "raw",
            "str",
            "int",
            "spans",
        ), "mode must be 'str' or 'int' or 'spans' or 'raw'"

        if not pathlib.Path(dictpath).exists():
            raise FileNotFoundError(f'File not found: {dictpath}')

        self.mode = mode
        self.dict = load_dictionary(dictpath)

    def __call__(self, text: str):
        clean_text = clean_whitespace(text)
        inputs = clean_text.lower()

        # Some safety checks before proceeding in int output mode
        if self.mode in ('int', 'str') and (text[0].isspace() or text[-1].isspace()):
                raise ValueError("Input text cannot start or end with whitespace in 'int' or 'str' mode.")

        words = inputs.split('\n')

        if self.mode == 'raw':
            return '\n'.join(hyphenate_words_simple(self.dict, words))

        wordparts = hyphenate_words_numbers(self.dict, words)
        whitespaces = (-len(m.group(0)) for m in whitespace_pattern.finditer(text))

        # Interleave the word chunk lengths with the whitespace
        lens = [
                   i
                   for wplens, wslen in zip_longest(wordparts, whitespaces, fillvalue=0)
                   for i in (*wplens, wslen)
               ][:-1]

        if self.mode == "int":
            return lens
        elif self.mode == "spans":
            return list(to_spans(lens, skip_whitespace=True))
        else:
            return [text[i:j] for i, j in to_spans(lens, skip_whitespace=False)]
