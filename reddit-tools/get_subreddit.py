#!/usr/bin/env python3

# Filter Reddit JSON data (https://files.pushshift.io/reddit/) by
# subreddit.

import sys
import os
import json
import logging

import zstandard as zstd

from argparse import ArgumentParser


def argparser():
    ap = ArgumentParser()
    ap.add_argument('subreddit')
    ap.add_argument('jsonl', nargs='+')
    return ap


def filter_reddit_stream(f, fn, args):
    out_count = 0
    for ln, line in enumerate(f, start=1):
        try:
            data = json.loads(line)
        except Exception as e:
            logging.error(f'failed to load JSON: {line}')
            continue

        try:
            subreddit = data['subreddit']
        except KeyError:
            logging.error(f'missing "subreddit": {data}')
            continue
            
        if subreddit != args.subreddit:
            continue
            
        print(line, end='')
        out_count += 1
        
    print(f'{os.path.basename(fn)}: processed {ln} entries,',
          f'output {out_count}.',
          file=sys.stderr)


def filter_reddit(fn, args):
    if not fn.endswith('.zst'):
        with open(fn) as f:
            filter_reddit_stream(f, fn, args)
    else:
        dctx = zstd.ZstdDecompressor(max_window_size=2**31)
        with zstd.open(fn, 'rt', dctx=dctx) as f:
            filter_reddit_stream(f, fn, args)


def main(argv):
    args = argparser().parse_args(argv[1:])

    for fn in args.jsonl:
        filter_reddit(fn, args)


if __name__ == '__main__':
    sys.exit(main(sys.argv))
