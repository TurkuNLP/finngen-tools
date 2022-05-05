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
DEFAULT_NORMALIZATION = 'NFKC'

# Escape characters for --include-space
SPACE_ESCAPE = '<S>'
TAB_ESCAPE = '<T>'
NEWLINE_ESCAPE = '<N>'

# Special cases for normalization
COMBINING_DIACRITICAL_MARKS = ''.join(chr(c) for c in range(0x0300, 0x036F+1))
REMOVE_COMBINING_CHARS = str.maketrans('', '', COMBINING_DIACRITICAL_MARKS)


def argparser():
    ap = ArgumentParser()
    ap.add_argument('-b', '--bert-vocab', default=None,
                    help='use given BERT vocab.txt instead of --tokenizer')
    ap.add_argument('-n', '--normalization', default=DEFAULT_NORMALIZATION,
                    help='unicode normalization')
    ap.add_argument('-s', '--no-space', default=False, action='store_true',
                    help='do not encode space characters')
    ap.add_argument('-u', '--allow-unk', default=False, action='store_true',
                    help='allow UNK token in output')
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


def warn_on_unk(text, tokenizer, tokens):
    if tokenizer.unk_token in tokens:
        for token in tokenizer.basic_tokenizer.tokenize(
                text, never_split=tokenizer.all_special_tokens):
            if tokenizer.unk_token in tokenizer.tokenize(token):
                logging.warning(
                    f'tokenize("{token}") = {tokenizer.tokenize(token)}'
                    f' ({token.encode("unicode-escape").decode("ascii")})'
                )


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


def tokenize_jsonl(fn, tokenizer, args):
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
            for line_tokens in tokenize(text, tokenizer, args):
                warn_on_unk(text, tokenizer, line_tokens)
                print(' '.join(line_tokens))


def get_tokenizer(args):
    if args.bert_vocab is None:
        tokenizer = transformers.AutoTokenizer.from_pretrained(
            args.tokenizer,
            use_fast=False
        )
    else:
        tokenizer = transformers.BertTokenizer(
            args.bert_vocab,
            do_lower_case=False
        )

    added_count = 0
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
