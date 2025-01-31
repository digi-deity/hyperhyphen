from functools import cache
import ctypes
import pathlib


dll = ctypes.windll.LoadLibrary(pathlib.Path(__file__).parent / 'libhyphenate.dll')

dll.hnj_hyphen_load.restype = ctypes.c_void_p
dll.hnj_hyphen_load.argtypes = (ctypes.c_char_p, )

dll.parse_word.restype = ctypes.c_int
dll.parse_word.argtypes = (ctypes.c_void_p, ctypes.c_char_p, ctypes.c_char_p, ctypes.c_int, ctypes.c_int, ctypes.c_int, ctypes.c_int, ctypes.c_int, ctypes.c_int)

dll.parse_words.restype = ctypes.c_int
dll.parse_words.argtypes = (ctypes.c_void_p, ctypes.c_char_p, ctypes.c_char_p, ctypes.c_int, ctypes.c_int, ctypes.c_int, ctypes.c_int, ctypes.c_int, ctypes.c_int)

def load_dictionary(path: str):
    return dll.hnj_hyphen_load(path.encode('utf-8'))

def hyphenate_words(dict, words: list[str], optn: bool, opts: bool, optnn: bool, optdd: bool):
    bwords = '\0'.join(words).encode('utf-8')
    buffer = ctypes.create_string_buffer(len(bwords)*2)
    result = dll.parse_words(dict, bwords, buffer, len(words), len(buffer), optn, opts, optnn, optdd)
    if result != 0:
        raise BufferError(f"Buffer overflow. Result is incomplete.")

    return buffer.value.decode('utf-8').split('\n')[:-1]

def hyphenate_words_numbers(dict, words: list[str]):
    out = hyphenate_words(dict, words, False, False, True, False)
    return [list(map(int, x.split())) for x in out]

def hyphenate_words_simple(dict, words: list[str]):
    return hyphenate_words(dict, words, False, True, False, False)