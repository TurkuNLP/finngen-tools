#!/usr/bin/env python3

# Print tokenized text from JSONL with field 'text'. Originally
# written to support building a language model with KenLM for ranking
# texts by perplexity.

import sys
import json
import unicodedata
import logging

import transformers

from argparse import ArgumentParser


DEFAULT_TOKENIZER = 'TurkuNLP/bert-base-finnish-cased-v1'

# Escape characters for --include-space
SPACE_ESCAPE = '<S>'
TAB_ESCAPE = '<T>'
NEWLINE_ESCAPE = '<N>'


def argparser():
    ap = ArgumentParser()
    ap.add_argument('-s', '--no-space', default=False, action='store_true',
                    help='do not encode space characters')
    ap.add_argument('-t', '--tokenizer', default=DEFAULT_TOKENIZER)
    ap.add_argument('jsonl', nargs='+')
    return ap


def tokenize(text, tokenizer, args):
    if args.no_space:
        for line in text.split('\n'):
            if line and not line.isspace():
                yield tokenizer.tokenize(line)
    else:
        # TODO other space characters
        text = text.replace(' ', f' {SPACE_ESCAPE} ')
        text = text.replace('\t', f' {TAB_ESCAPE} ')
        text = text.replace('\n', f' {NEWLINE_ESCAPE} ')
        yield tokenizer.tokenize(text)


def tokenize_jsonl(fn, tokenizer, args):
    with open(fn) as f:
        for ln, line in enumerate(f, start=1):
            try:
                data = json.loads(line)
                text = data['text']
            except:
                logging.error(f'parsing line {ln} in {fn}: {line}')
                raise
            for line_tokens in tokenize(text, tokenizer, args):
                print(' '.join(line_tokens))


def get_tokenizer(args):
    tokenizer = transformers.AutoTokenizer.from_pretrained(
        args.tokenizer,
        use_fast=False
    )

    # Make sure all non-control, non-space 7-bit ASCII chars are included
    include_chars = [
        chr(i) for i in range(128)
        if (not unicodedata.category(chr(i)).startswith('C') and
            not chr(i).isspace())
    ]
    added_count = tokenizer.add_tokens(include_chars)
    if not args.no_space:
        added_count += tokenizer.add_tokens([
            SPACE_ESCAPE, TAB_ESCAPE, NEWLINE_ESCAPE
        ])
    if added_count:
        logging.warning(f'added {added_count} tokens')
    
    return tokenizer


def main(argv):
    args = argparser().parse_args(argv[1:])

    tokenizer = get_tokenizer(args)
    
    for fn in args.jsonl:
        tokenize_jsonl(fn, tokenizer, args)


if __name__ == '__main__':
    sys.exit(main(sys.argv))
