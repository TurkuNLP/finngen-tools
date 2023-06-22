#!/usr/bin/env python3

# Filter JSONL `text` field lines with a KenLM model perplexity threshold.

import sys
import re
import json
import unicodedata

import kenlm

from logging import warning
from argparse import ArgumentParser

from berttokenizer import basic_tokenize


# Default key for the perplexity value in JSONL
DEFAULT_KEY = 'ppl_kenlm'

# Value to return on overflow
VERY_LARGE_PPL_VALUE = 10**30


def argparser():
    ap = ArgumentParser()
    ap.add_argument('--min-remaining', default=None, type=float, help=
                    'minimum ratio of chars after filtering. If lower, '
                    'remove the entire document.')
    ap.add_argument('model', help='KenLM model')
    ap.add_argument('threshold', type=int, help='perplexity threshold')
    ap.add_argument('jsonl', nargs='+')
    return ap


def is_punct(string):
    return all(unicodedata.category(c).startswith('P') for c in string)


def word_count(tokenized):
    return sum(not is_punct(t) for t in tokenized)


def tokenize(text):
    for line in text.split('\n'):
        if line and not line.isspace():
            yield basic_tokenize(line)


def perplexity(text, model):
    score, words = 0, 0
    for tokenized in tokenize(text):
        score += model.score(' '.join(tokenized))
        words += word_count(tokenized) + 1 # +1 for EOS
    try:
        return 10**(-score/words)
    except Exception as e:
        warning(f'{e}: 10**-({score}/{words})')
        return VERY_LARGE_PPL_VALUE


def filter_lines(text, model, args):
    lines = text.split('\n')

    filtered = []
    for line in lines:
        if line.isspace() or not line:
            filtered.append(line)    # keep blanks (TODO: add arg?)
            continue
        ppl = perplexity(line, model)
        if ppl < args.threshold:
            filtered.append(line)

    # Don't alter spacing if no lines were removed
    if len(filtered) == len(lines):
        return text

    # Heuristically repair space
    while filtered and (filtered[0].isspace() or not filtered[0]):
        filtered = filtered[1:]
    while filtered and (filtered[-1].isspace() or not filtered[-1]):
        filtered = filtered[:-1]
    filtered_text = '\n'.join(filtered)
    filtered_text = re.sub(r'\n\s*\n', '\n\n', filtered_text)

    remaining = len(filtered_text)/len(text)
    if args.min_remaining is not None and remaining < args.min_remaining:
        return ''

    return filtered_text


def filter_by_perplexity(fn, model, args):
    orig_chars, filt_chars = 0, 0
    with open(fn) as f:
        for ln, line in enumerate(f, start=1):
            try:
                data = json.loads(line)
                text = data['text']
            except:
                logging.error(f'parsing line {ln} in {fn}: {line}')
                raise

            orig_chars += len(text)
            text = filter_lines(text, model, args)
            filt_chars += len(text)

            if text.isspace() or not text:
                continue    # emptied entirely
            
            data['text'] = text
            print(json.dumps(data, ensure_ascii=False))

    print(f'filtered {fn} to {filt_chars}/{orig_chars} ({filt_chars/orig_chars:.1%})', file=sys.stderr)


def main(argv):
    args = argparser().parse_args(argv[1:])

    print(f'loading model ... ', file=sys.stderr, end='', flush=True)
    model = kenlm.Model(args.model)
    print(f'done.', file=sys.stderr, flush=True)

    for fn in args.jsonl:
        filter_by_perplexity(fn, model, args)


if __name__ == '__main__':
    sys.exit(main(sys.argv))
