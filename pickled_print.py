import sys

from itertools import islice
from argparse import ArgumentParser

from transformers import AutoTokenizer
from pickled import PickledDataset


def argparser():
    ap = ArgumentParser()
    ap.add_argument('pickle', nargs='+')
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

    for fn in args.pickle:
        for example in islice(PickledDataset(fn), 0, args.limit, args.step):
            for k, v in example.items():
                print(k, list(v))
            if tokenizer:
                decoded = tokenizer.decode(example['input_ids'])
                print('decoded', repr(decoded))


if __name__ == '__main__':
    sys.exit(main(sys.argv))
