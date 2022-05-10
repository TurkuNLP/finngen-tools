#!/usr/bin/env python3

# Add KenLM model perplexity value to JSONL with text as 'text'.

import sys
import json
import unicodedata

import kenlm

from argparse import ArgumentParser

from berttokenizer import basic_tokenize


# Default key for the perplexity value in JSONL
DEFAULT_KEY = 'ppl_kenlm'


def argparser():
    ap = ArgumentParser()
    ap.add_argument('-k', '--key', default=DEFAULT_KEY, 
                    help='key for perplexity value')
    ap.add_argument('model', help='KenLM model')
    ap.add_argument('jsonl', nargs='+')
    return ap


def is_punct(string):
    return all(unicodedata.category(c).startswith('P') for c in string)


def word_count(tokenized, args):
    return sum(not is_punct(t)) for t in tokenized)


def tokenize(text, args):
    for line in text.split('\n'):
        if line and not line.isspace():
            yield basic_tokenize(line)


def add_perplexity(fn, model, args):
    with open(fn) as f:
        for ln, line in enumerate(f, start=1):
            try:
                data = json.loads(line)
                text = data['text']
            except:
                logging.error(f'parsing line {ln} in {fn}: {line}')
                raise

            total_score, total_words = 0, 0
            for tokenized in tokenize(text, args):
                total_score += model.score(' '.join(tokenized))
                total_words += word_count(tokenized, args) + 1 # +1 for EOS
            perplexity = 10**(-total_score/total_words)

            assert args.key not in data['meta']
            data['meta'][args.key] = int(perplexity)

            if ln % 100 == 0:
                print(f'Processed {ln} ...', file=sys.stderr, flush=True)
                flush = True
            else:
                flush = False
            print(json.dumps(data, ensure_ascii=False), flush=flush)


def main(argv):
    args = argparser().parse_args(argv[1:])

    print(f'loading model ... ', file=sys.stderr, end='', flush=True)
    model = kenlm.Model(args.model)
    print(f'done.', file=sys.stderr, flush=True)
    
    for fn in args.jsonl:
        add_perplexity(fn, model, args)


if __name__ == '__main__':
    sys.exit(main(sys.argv))
