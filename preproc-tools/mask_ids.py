#!/usr/bin/env python3

import sys
import json
import regex

from multiprocessing import Pool
from argparse import ArgumentParser


# High-recall re for Finnish national identification numbers
NII_RE = regex.compile(r'\b[[:digit:]]{6}[A+-][[:digit:]]{3}[[:digit:]A-Z]\b')


def argparser():
    ap = ArgumentParser()
    ap.add_argument('-n', '--num-workers', type=int, default=16)
    ap.add_argument('jsonl', nargs='+')
    return ap


def mask_ids(string, nii_replacement='010101-001Z'):
    nii_spans = []
    for m in NII_RE.finditer(string):
        nii_spans.append((m.start(), m.end()))

    for start, end in reversed(nii_spans):
        before, nii, after = string[:start], string[start:end], string[end:]
        string = before + nii_replacement + after

    return string


def mask_json_ids(line):
    data = json.loads(line)
    text = data['text']
    text = mask_ids(text)
    data['text'] = text
    return json.dumps(data, ensure_ascii=False)


def main(argv):
    args = argparser().parse_args(argv[1:])

    with Pool(args.num_workers) as pool:
        for fn in args.jsonl:
            with open(fn) as f:
                for l in pool.imap(mask_json_ids, f, chunksize=1024):
                    print(l)


if __name__ == '__main__':
    sys.exit(main(sys.argv))
