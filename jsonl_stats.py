#!/usr/bin/env python3

# Provide basic corpus statistics for JSONL format with one document
# per line and document text as 'text'.

import sys
import json

from argparse import ArgumentParser

from berttokenizer import basic_tokenize


def argparser():
    ap = ArgumentParser()
    ap.add_argument('jsonl', nargs='+')
    return ap


def sifmt(i):
    affix = iter(['', 'K', 'M', 'G', 'T', 'P', 'E'])
    while i > 1000:
        i /= 1000
        next(affix)
    return f'{i:.1f}{next(affix)}'


def get_jsonl_stats(fn, args):
    docs, words, chars = 0, 0, 0
    with open(fn) as f:
        for ln, line in enumerate(f):
            data = json.loads(line)
            text = data['text']
            docs += 1
            words += len(basic_tokenize(text))
            chars += len(text)
    return docs, words, chars


def main(argv):
    args = argparser().parse_args(argv[1:])

    docs, words, chars = 0, 0, 0
    for fn in args.jsonl:
        file_docs, file_words, file_chars = get_jsonl_stats(fn, args)
        docs += file_docs
        words += file_words
        chars += file_chars

    print('|docs|words|chars|')
    print('|----|-----|-----|')
    print(f'|{docs}|{words}|{chars}|')
    print(f'|({sifmt(docs)})|({sifmt(words)})|({sifmt(chars)})|')


if __name__ == '__main__':
    sys.exit(main(sys.argv))
