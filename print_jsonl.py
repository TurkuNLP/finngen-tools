#!/usr/bin/env python3

import sys
import json

from random import random
from argparse import ArgumentParser


def argparser():
    ap = ArgumentParser()
    ap.add_argument('-n', '--no-header', action='store_true')
    ap.add_argument('-r', '--ratio', default=None, type=float)
    ap.add_argument('jsonl', nargs='+')
    return ap


def main(argv):
    args = argparser().parse_args()

    for fn in args.jsonl:
        with open(fn) as f:
            for ln, l in enumerate(f, start=1):
                if args.ratio and random() > args.ratio:
                    continue
                data = json.loads(l)
                if not args.no_header:
                    print('-'*20, data['id'], '-'*20)
                print(data['text'])


if __name__ == '__main__':
    sys.exit(main(sys.argv))
