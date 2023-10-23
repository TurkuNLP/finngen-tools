#!/usr/bin/env python3

# Print tokenized text from JSONL with field 'text'. Originally
# written to support building a language model with KenLM for ranking
# texts by perplexity.

import sys
import json
import unicodedata
import logging

from argparse import ArgumentParser

from berttokenizer import basic_tokenize


# Unicode normalization
DEFAULT_NORMALIZATION = 'NFKC'

# Special cases for normalization
COMBINING_DIACRITICAL_MARKS = ''.join(chr(c) for c in range(0x0300, 0x036F+1))
REMOVE_COMBINING_CHARS = str.maketrans('', '', COMBINING_DIACRITICAL_MARKS)


def argparser():
    ap = ArgumentParser()
    ap.add_argument('-n', '--normalization', default=DEFAULT_NORMALIZATION,
                    help='unicode normalization')
    ap.add_argument('jsonl', nargs='+')
    return ap


def tokenize(text, args):
    for line in text.split('\n'):
        if line and not line.isspace():
            yield basic_tokenize(line)


def remove_combining_chars(string):
    return string.translate(REMOVE_COMBINING_CHARS)


def normalize(text, args):
    # Tokenization edge cases
    text = text.replace(' ́', "'")

    text = unicodedata.normalize(args.normalization, text)

    if args.normalization.endswith('C'):
        # composition normalization, no combining chars should remain
        text = remove_combining_chars(text)

    return text


def tokenize_jsonl(fn, args):
    with open(fn) as f:
        for ln, line in enumerate(f, start=1):
            try:
                data = json.loads(line)
                text = data['text']
            except:
                logging.error(f'parsing line {ln} in {fn}: {line}')
                raise
            try:
                text = normalize(text, args)
            except:
                logging.error(f'normalizing line {ln} in {fn}: {text}')
                raise
            for line_tokens in tokenize(text, args):
                print(' '.join(line_tokens))


def main(argv):
    args = argparser().parse_args(argv[1:])

    for fn in args.jsonl:
        tokenize_jsonl(fn, args)


if __name__ == '__main__':
    sys.exit(main(sys.argv))
