import ctypes.util
import pathlib
import sys
from ctypes import *
from functools import cache

_libs_info, _libs = {}, {}

def _find_library(name, dirs, search_sys):
    if sys.platform in ("win32", "cygwin", "msys"):
        patterns = ["{}.dll", "lib{}.dll", "{}"]
    elif sys.platform == "darwin":
        patterns = ["lib{}.dylib", "{}.dylib", "lib{}.so", "{}.so", "{}"]
    else:  # assume unix pattern or plain name
        patterns = ["lib{}.so", "{}.so", "{}"]

    for dir in dirs:
        dir = pathlib.Path(dir)
        if not dir.is_absolute():
            dir = (pathlib.Path(__file__).parent / dir).resolve(strict=False)
        for pat in patterns:
            libpath = dir / pat.format(name)
            if libpath.is_file():
                return str(libpath)

    libpath = ctypes.util.find_library(name) if search_sys else None
    if not libpath:
        raise ImportError(f"Could not find library '{name}' (dirs={dirs}, search_sys={search_sys})")

    return libpath

def _register_library(name, dllclass, **kwargs):
    libpath = _find_library(name, **kwargs)
    _libs_info[name] = {**kwargs, "path": libpath}
    _libs[name] = dllclass(libpath)

_register_library(
    name='hyphenate',
    dllclass=ctypes.CDLL,
    dirs=['.'],
    search_sys=False,
)

class struct_hyphendict (Structure):
    pass

HyphenDict = POINTER(struct_hyphendict)

libhyphenate = _libs['hyphenate']

libhyphenate.hnj_hyphen_load.restype = HyphenDict
libhyphenate.hnj_hyphen_load.argtypes = (c_char_p, )

libhyphenate.parse_word.restype = c_int
libhyphenate.parse_word.argtypes = (HyphenDict, c_char_p, c_char_p, c_int, c_int, c_int, c_int, c_int, c_int)

libhyphenate.parse_words.restype = c_int
libhyphenate.parse_words.argtypes = (HyphenDict, c_char_p, c_char_p, c_int, c_int, c_int, c_int, c_int, c_int)

@cache
def load_dictionary(path: str):
    return libhyphenate.hnj_hyphen_load(path.encode('utf-8'))

def hyphenate_words(dict, words: list[str], optn: bool, opts: bool, optnn: bool, optdd: bool):
    bwords = '\0'.join(words).encode('utf-8')
    buffer = create_string_buffer(len(bwords)*2)
    result = libhyphenate.parse_words(dict, bwords, buffer, len(words), len(buffer), optn, opts, optnn, optdd)
    if result != 0:
        raise BufferError(f"Buffer overflow. Result is incomplete.")

    return buffer.value.decode('utf-8').split('\n')[:-1]

def hyphenate_words_numbers(dict, words: list[str]):
    out = hyphenate_words(dict, words, False, False, True, False)
    return [list(map(int, x.split())) for x in out]

def hyphenate_words_simple(dict, words: list[str]):
    return hyphenate_words(dict, words, False, True, False, False)