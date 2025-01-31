import pytest
from hyperhyphen import Hyphenator
import re

def test_hyperhyphen_raw():
    h = Hyphenator(mode='raw')
    str_output = h("reconciliation microprocessing\t\tmiracle      messaging character 𱍊character 𱍊character𱍊")
    target = "recon=cil=i=a=tion\nmicro=pro=cess=ing\nmira=cle\nmessag=ing\nchar=ac=ter\n𱍊char=ac=ter\n𱍊char=ac=ter𱍊"
    assert str_output == target

def test_hyperhyphen_str():
    hs = Hyphenator(mode='str')
    hr = Hyphenator(mode='raw')

    words = """reconciliation microprocessing\t\tmiracle      messaging character 𱍊character 𱍊character𱍊"""

    raw_output = hr(words)
    str_output = hs(words)

    str2raw = '='.join(str_output)
    str2raw = re.sub(r'=\s+=', '\n', str2raw)

    assert str2raw == raw_output

def test_hyperhyphen_strip_error():
    h = Hyphenator(mode='int')

    with pytest.raises(ValueError):
        h(" batmobile ")

    h = Hyphenator(mode='str')

    with pytest.raises(ValueError):
        h(" batmobile ")

def test_hyperhyphen_buffer_protection():
    bufsize = 1024
    h = Hyphenator(mode='raw', bufsize=bufsize)

    h("x " * ((bufsize - 1) // 2))

    with pytest.raises(AssertionError):
        h("x " * ((bufsize + 1) // 2))