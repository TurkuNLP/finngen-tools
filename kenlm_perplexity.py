#!/usr/bin/env python3

# Add KenLM model perplexity value to JSONL with text as 'text'.

import sys
import json

import kenlm

from argparse import ArgumentParser

# Tokenizer and text escaping need to match the script that was used
# to prepare texts to build the language model, here assumed to have
# been tokenizer_jsonl.py
from tokenize_jsonl import DEFAULT_TOKENIZER, get_tokenizer, tokenize


# Key for the perplexity value in JSONL
PPL_KEY = 'kenlm_perplexity'


def argparser():
    ap = ArgumentParser()
    ap.add_argument('-s', '--no-space', default=False, action='store_true',
                    help='do not encode space characters')
    ap.add_argument('-t', '--tokenizer', default=DEFAULT_TOKENIZER)
    ap.add_argument('model', help='KenLM model')
    ap.add_argument('jsonl', nargs='+')
    return ap


def add_kenlm_perplexity(fn, tokenizer, model, args):
    with open(fn) as f:
        for ln, line in enumerate(f, start=1):
            try:
                data = json.loads(line)
                text = data['text']
            except:
                logging.error(f'parsing line {ln} in {fn}: {line}')
                raise

            total_score, total_words = 0, 0
            for tokenized in tokenize(text, tokenizer, args):
                total_score += model.score(' '.join(tokenized))
                total_words += len(tokenized) + 1 # +1 for EOS
            perplexity = 10**(-total_score/total_words)

            assert PPL_KEY not in data['meta']
            data['meta'][PPL_KEY] = int(perplexity)

            print(json.dumps(data, ensure_ascii=False))


def main(argv):
    args = argparser().parse_args(argv[1:])

    tokenizer = get_tokenizer(args)
    model = kenlm.Model(args.model)
    
    for fn in args.jsonl:
        add_kenlm_perplexity(fn, tokenizer, model, args)


if __name__ == '__main__':
    sys.exit(main(sys.argv))
