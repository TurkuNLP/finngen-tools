#!/usr/bin/env python3

import sys
import json

import fasttext

from collections import Counter
from argparse import ArgumentParser


LABEL_PREFIX = '__label__'

TOXICITY_LABELS = [
    'toxicity',
    'severe_toxicity',
    'obscene',
    'insult',
    'identity_attack',
    'threat',
]


def argparser():
    ap = ArgumentParser()
    ap.add_argument('-i', '--invert', action='store_true')
    ap.add_argument('model')
    ap.add_argument('jsonl', nargs='+')
    return ap


def is_toxic(text, model, counts):
    text = ' '.join(text.split())
    labels, values = model.predict(text, k=-1, threshold=0.5, on_unicode_error='replace')

    toxic_label_seen = False
    for l in labels:
        assert l.startswith(LABEL_PREFIX)
        l = l.replace(LABEL_PREFIX, '')
        if l in TOXICITY_LABELS:
            toxic_label_seen = True
            counts[l] += 1

    return toxic_label_seen


def main(argv):
    args = argparser().parse_args(argv[1:])

    model = fasttext.load_model(args.model)

    counts, total = Counter(), 0
    for fn in args.jsonl:
        with open(fn) as f:
            for ln, l in enumerate(f, start=1):
                data = json.loads(l)
                text = data['text']
                remove = is_toxic(text, model, counts)
                if args.invert:
                    remove = not remove
                if not remove:
                    print(l, end='')
                total += 1

    for l in TOXICITY_LABELS:
        if l in counts:
            print(f'{l}: {counts[l]}/{total} ({counts[l]/total:.1%})',
                  file=sys.stderr)


if __name__ == '__main__':
    sys.exit(main(sys.argv))
