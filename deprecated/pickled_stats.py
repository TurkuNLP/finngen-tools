import sys

from collections import Counter
from argparse import ArgumentParser

from pickled import PickledDataset


def argparser():
    ap = ArgumentParser()
    ap.add_argument('pickle', nargs='+')
    return ap


def main(argv):
    args = argparser().parse_args(argv[1:])

    for fn in args.pickle:
        stats = Counter()
        for example in PickledDataset(fn):
            for k, v in example.items():
                stats[f'{k}[{len(v)}]'] += 1
            stats['TOTAL'] += 1
        for k, v in reversed(sorted(stats.items())):
            print(f'{fn}: {v} {k}')


if __name__ == '__main__':
    sys.exit(main(sys.argv))

