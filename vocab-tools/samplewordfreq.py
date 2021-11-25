#!/usr/bin/env python3

import sys
import os
import logging

import chardet
import ftfy

from argparse import ArgumentParser


logging.basicConfig()
logger = logging.getLogger(os.path.basename(__file__))


# Default downsampling ratio
DEFAULT_RATIO = 0.01


def argparser():
    ap = ArgumentParser()
    ap.add_argument(
        '--ratio',
        default=DEFAULT_RATIO,
        type=float,
        help='downsampling ratio'
    )
    ap.add_argument(
        '--quiet',
        default=False,
        action='store_true',
        help='suppress warnings'
    )
    ap.add_argument(
        'freqs',
        help='word frequencies'
    )
    return ap


def parse_initial_number(line):
    # Parse initial sequence of digits with optional surrounding
    # whitespace. Operates on bytes to support potentially mixed
    # encodings.
    i = 0
    while i < len(line) and line[i] in b' \t':
        i += 1
    j = i
    while j < len(line) and line[j] in b'0123456789':
        j += 1
    if j == 0 or j == len(line):
        raise ValueError(f'failed to separate number (at {i}: {line})')
    number = int(line[i:j])
    k = 0
    while k < len(line) and line[k] in b' \t':
        k += 1
    return number, line[j:]


def downsample_word_freqs(fn, args):
    encoding_errors, parsing_errors = 0, 0
    with open(args.freqs, 'rb') as f:
        for ln, line in enumerate(f, start=1):
            line = line.rstrip(b'\n')
            freq, word = parse_initial_number(line)
            new_freq = int(round(freq * args.ratio))
            if new_freq == 0:
                continue    # downsampled away
            detected = chardet.detect(word)
            encoding = detected['encoding']
            if encoding is None:
                encoding = 'utf-8'    # try anyway
            try:
                word = word.decode()
            except Exception as e:
                logger.warning(f'could not decode word with frequency {freq}, '
                               f'encoding {encoding} on line {ln} in {fn}:'
                               f'"{word}" ({e})')
                encoding_errors += 1
                continue
            word = ftfy.fix_encoding(word)
            print(new_freq, word.rstrip())
    if encoding_errors:
        print(f'Encountered {encoding_errors} encoding errors in {fn}',
              file=sys.stderr)


def main(argv):
    args = argparser().parse_args(argv[1:])

    if args.quiet:
        logger.setLevel(logging.ERROR)

    downsample_word_freqs(args.freqs, args)


if __name__ == '__main__':
    sys.exit(main(sys.argv))
