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


class struct_hyphendict(Structure):
    pass


HyphenDict = POINTER(struct_hyphendict)

libhyphenate = _libs['hyphenate']

libhyphenate.hnj_hyphen_load.restype = HyphenDict
libhyphenate.hnj_hyphen_load.argtypes = (c_char_p,)

libhyphenate.parse_word.restype = c_int
libhyphenate.parse_word.argtypes = (HyphenDict, c_char_p, c_char_p, c_int, c_int, c_int, c_int, c_int, c_int)

libhyphenate.parse_words.restype = c_int
libhyphenate.parse_words.argtypes = (HyphenDict, c_char_p, c_char_p, c_int, c_int, c_int, c_int, c_int, c_int)

@cache
def load_dictionary(path: str):
    if not path or len(path.encode('utf-8')) > 4096:  # Reasonable path length limit
        raise ValueError("Invalid dictionary path")

    dict_ptr = libhyphenate.hnj_hyphen_load(path.encode('utf-8'))
    if not dict_ptr:
        raise RuntimeError(f"Failed to load dictionary: {path}")

    return dict_ptr


def hyphenate_words(dict, words: list[str], optn: bool, opts: bool, optnn: bool, optdd: bool):
    if not dict:
        raise ValueError("Dictionary pointer is null")

    if not words:
        return []

    # Validate input words
    for word in words:
        if not isinstance(word, str):
            raise TypeError("All words must be strings")
        if len(word.encode('utf-8')) > 1024:  # Reasonable word length limit
            raise ValueError(f"Word too long: {word[:50]}...")

    # Calculate safe buffer size with generous margin
    bwords = '\0'.join(words).encode('utf-8')
    input_size = len(bwords)

    # Use much larger buffer to prevent overflow - hyphenation can significantly expand text
    buffer_size = max(input_size * 4, 8192)  # At least 4x input size or 8KB minimum

    try:
        buffer = create_string_buffer(buffer_size)

        result = libhyphenate.parse_words(
            dict, bwords, buffer, len(words), buffer_size,
            int(optn), int(opts), int(optnn), int(optdd)
        )

        if result != 0:
            raise BufferError(f"Hyphenation failed with error code: {result}")

        # Ensure null termination
        buffer_content = buffer.value.decode('utf-8')

        # Validate output format
        output_lines = buffer_content.split('\n')
        if output_lines and output_lines[-1] == '':
            output_lines = output_lines[:-1]

        if len(output_lines) != len(words):
            raise RuntimeError(f"Output mismatch: expected {len(words)} lines, got {len(output_lines)}")

        return output_lines

    except UnicodeDecodeError:
        raise RuntimeError("Invalid UTF-8 output from hyphenation library")


def hyphenate_words_numbers(dict, words: list[str]):
    if not words:
        return []

    out = hyphenate_words(dict, words, False, False, True, False)
    result = []

    for i, line in enumerate(out):
        try:
            numbers = list(map(int, line.split()))
            result.append(numbers)
        except ValueError:
            raise RuntimeError(f"Invalid numeric output for word {i}: '{line}'")

    return result


def hyphenate_words_simple(dict, words: list[str]):
    return hyphenate_words(dict, words, False, True, False, False)