# HyperHyphen

HyperHyphen is a Python package that provides hyper fast word hyphenation.
It supports multiple languages and allows for easy integration into Python applications.

This is not a feature complete implementation of the Hyphenator library. There are better libraries for hyphenation,
such as [PyHyphen](https://github.com/hrbrmstr/pyhyphen) or [Pyphen](https://github.com/Kozea/Pyphen).

This library will only suggest hyphenation points, without consideration of word modification or 
language-specific rules. You don't need to worry about irregular hyphenation and word-modification
if the line-breaking / wrapping algorithm can pick from many other hyphenation points instead. This library hyphenation 
loop is completely written in C to ensure that plenty of such points can be suggested fast.

## Installation
You can install HyperHyphen using pip:

```bash
pip install hyperhyphen
```

## Usage

Looking at your code, I can see the package supports multiple output modes. Here are usage examples to add to your `README.md`:

## Usage

### Basic Usage

```python
from hyperhyphen import Hyphenator

# Create a hyphenator for English (US)
h = Hyphenator(language="en_US")

# Hyphenate text (default "str" mode)
text = "reconciliation microprocessing"
result = h(text)
print(result)
# Output: ['recon', 'cil', 'i', 'a', 'tion', ' ', 'micro', 'pro', 'cess', 'ing']
```

### Different Output Modes

HyperHyphen supports four different output modes:

#### String Mode ("str") - Default
Returns a list of hyphenated word parts and whitespace segments:
```python
h = Hyphenator(mode="str", language="en_US")
result = h("The internationalization committee discussed 'telecommunications infrastructure modernization,' but extraordinary circumstances required unprecedented organizational transformations.")
print(result)
# Output: ['The', ' ', 'inter', 'na', 'tion', 'al', 'iza', 'tion', ' ', 'commit', 'tee', ' ', 'discussed', ' ', "'telecom", 'mu', 'ni', 'ca', 'tions', ' ', 'infra', 'struc', 'ture', ' ', 'modern', 'iza', "tion,'", ' ', 'but', ' ', 'extra', 'or', 'di', 'nary', ' ', 'circum', 'stances', ' ', 'required', ' ', 'unprece', 'dented', ' ', 'orga', 'ni', 'za', 'tional', ' ', 'trans', 'for', 'ma', 'tions.']
```

#### Raw Mode ("raw")
Returns hyphenated words with `=` separators, preserving original whitespace structure:
```python
h = Hyphenator(mode="raw", language="en_US")
result = h("The internationalization committee discussed 'telecommunications infrastructure modernization,' but extraordinary circumstances required unprecedented organizational transformations.")
print(result)
# Output: "the\\ninter=na=tion=al=iza=tion\\ncommit=tee\\ndiscussed\\n\'telecom=mu=ni=ca=tions\\ninfra=struc=ture\\nmodern=iza=tion,\'\\nbut\\nextra=or=di=nary\\ncircum=stances\\nrequired\\nunprece=dented\\norga=ni=za=tional\\ntrans=for=ma=tions."
```

#### Integer Mode ("int")
Returns segment lengths as integers (positive for words, negative for whitespace):
```python
h = Hyphenator(mode="int", language="en_US")
result = h("The internationalization committee discussed 'telecommunications infrastructure modernization,' but extraordinary circumstances required unprecedented organizational transformations.")
print(result)
# Output: [3, -1, 5, 2, 4, 2, 3, 4, -1, 6, 3, -1, 9, -1, 8, 2, 2, 2, 5, -1, 5, 5, 4, -1, 6, 3, 6, -1, 3, -1, 5, 2, 2, 4, -1, 6, 7, -1, 8, -1, 7, 6, -1, 4, 2, 2, 6, -1, 5, 3, 2, 6]
```

#### Spans Mode ("spans")
Returns (start, end) tuples for word segments only (excluding whitespace):
```python
h = Hyphenator(mode="spans", language="en_US")
result = h("The internationalization committee discussed 'telecommunications infrastructure modernization,' but extraordinary circumstances required unprecedented organizational transformations.")
print(result)
# Output: [(0, 3), (4, 9), (9, 11), (11, 15), (15, 17), (17, 20), (20, 24), (25, 31), (31, 34), (35, 44), (45, 53), (53, 55), (55, 57), (57, 59), (59, 64), (65, 70), (70, 75), (75, 79), (80, 86), (86, 89), (89, 95), (96, 99), (100, 105), (105, 107), (107, 109), (109, 113), (114, 120), (120, 127), (128, 136), (137, 144), (144, 150), (151, 155), (155, 157), (157, 159), (159, 165), (166, 171), (171, 174), (174, 176), (176, 182)]
```

### Language Support

You can specify different languages using language codes:
```python
# German hyphenation
h_de = Hyphenator(language="de_DE")

# French hyphenation  
h_fr = Hyphenator(language="fr_FR")
```

## Requirements

- Python 3.9+

## License

This project is licensed under the Apache 2.0 license.