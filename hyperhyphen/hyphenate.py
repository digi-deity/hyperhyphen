import os
import re
import subprocess
from itertools import zip_longest, chain, accumulate
from typing import Literal

whitespace_pattern = re.compile(r'\s+')

def clean_whitespace(text: str) -> str:
    """Hyphenation is only defined for words. This function breaks the text into words seperated by newline characters."""
    return whitespace_pattern.sub('\n', text)

class Hyphenator:
    DEFAULT_BUFSIZE = 128 * 1024

    def __init__(self, dictpath: str = '/usr/share/hyphen/hyph_en_US.dic', mode: Literal['raw', 'str', 'int'] = 'str',
                 bufsize: int = DEFAULT_BUFSIZE):
        assert mode in ('raw', 'str', 'int'), "mode must be 'str' or 'int' or 'raw'"
        self.mode = mode
        self.bufsize = bufsize
        libhyphen = os.path.join(os.path.dirname(__file__), 'lib', 'hyphenate')
        self.proc = subprocess.Popen(
            [libhyphen, '-s' if mode == 'raw' else '-nn', dictpath],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=False,
            bufsize=bufsize,
        )

    def __call__(self, text: str) -> str:
        clean_text = clean_whitespace(text)
        n = clean_text.count('\n')
        inputs = clean_text.lower().encode('utf-8')

        assert len(inputs) < self.bufsize, "Too much text to hyphenate at once. Try to call in batches."

        # Some safety checks before proceding in int output mode
        if self.mode in ('int', 'str') and (text[0].isspace() or text[-1].isspace()):
                raise ValueError("Input text cannot start or end with whitespace in 'int' or 'str' mode.")

        self.proc.stdin.write(inputs)
        self.proc.stdin.write(b'\n')
        self.proc.stdin.flush()

        output = b''.join(self.proc.stdout.readline() for _ in range(n+1))[:-1]

        if self.mode == 'raw':
            return output.decode('utf-8')

        wordparts = ((int(i) for i in l.split(b' ')) for l in output.strip().split(b'\n'))
        whitespaces = (-len(m.group(0)) for m in whitespace_pattern.finditer(text))

        # Interleave the word chunk lengths with the whitespace
        lens = [i for wplens, wslen in zip_longest(wordparts, whitespaces, fillvalue=0) for i in (*wplens, wslen)][:-1]

        if self.mode == 'int':
            return lens

        acc = chain((0,), accumulate(map(abs, lens)))
        return [text[a:a + l] for a, l in zip(acc, map(abs, lens))]