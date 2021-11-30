#!/usr/bin/env python3

# Print contents of files in the indexed format

import sys

from itertools import islice
from argparse import ArgumentParser

from transformers import AutoTokenizer
from megatron.data import indexed_dataset


def argparser():
    ap = ArgumentParser()
    ap.add_argument('prefix', nargs='+')
    ap.add_argument('-l', '--limit', type=int, default=None)
    ap.add_argument('-s', '--step', type=int, default=1)
    ap.add_argument('-t', '--tokenizer', default=None)
    return ap


def main(argv):
    args = argparser().parse_args(argv[1:])

    if args.tokenizer is None:
        tokenizer = None
    else:
        tokenizer = AutoTokenizer.from_pretrained(args.tokenizer)

    for fn in args.prefix:
        dataset = indexed_dataset.make_dataset(fn, 'infer')
        for example in islice(dataset, 0, args.limit, args.step):
            print(example)
            if tokenizer:
                decoded = tokenizer.decode(example)
                print('decoded', repr(decoded))


if __name__ == '__main__':
    sys.exit(main(sys.argv))
