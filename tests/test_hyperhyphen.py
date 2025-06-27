import os
import pytest
from hyperhyphen import Hyphenator
from hyperhyphen.core import whitespace_pattern
import re
import pathlib

DIR = pathlib.Path(__file__).parent.resolve(strict=False)

LANGUAGE = 'en_US'

def test_hyperhyphen_raw():
    h = Hyphenator(mode="raw", language=LANGUAGE)
    str_output = h(
        "reconciliation microprocessing\t\tmiracle      messaging character 𱍊character 𱍊character𱍊"
    )
    target = "recon=cil=i=a=tion\nmicro=pro=cess=ing\nmira=cle\nmessag=ing\nchar=ac=ter\n𱍊char=ac=ter\n𱍊char=ac=ter𱍊"
    assert str_output == target


def test_hyperhyphen_str():
    hs = Hyphenator(mode="str", language=LANGUAGE)
    hr = Hyphenator(mode="raw", language=LANGUAGE)

    words = """reconciliation microprocessing\t\tmiracle      messaging character 𱍊character 𱍊character𱍊"""

    raw_output = hr(words)
    str_output = hs(words)

    str2raw = "=".join(str_output)
    str2raw = re.sub(r"=\s+=", "\n", str2raw)

    assert str2raw == raw_output


def test_hyperhyphen_syllables():
    h = Hyphenator(mode="spans", language=LANGUAGE)
    words = """reconciliation microprocessing\t\tmiracle      messaging character 𱍊character 𱍊character𱍊"""
    n_words = whitespace_pattern.sub(" ", words).count(" ") + 1
    output = h(words)
    concat = "".join([words[i:j] for i, j in output])

    assert concat == ''.join(filter(lambda x: not x.isspace(), words))
    assert len(output) > n_words


def test_hyperhyphen_strip_error():
    h = Hyphenator(mode="int", language=LANGUAGE)

    with pytest.raises(ValueError):
        h(" batmobile ")

    h = Hyphenator(mode="str", language=LANGUAGE)

    with pytest.raises(ValueError):
        h(" batmobile ")
