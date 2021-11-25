#!/usr/bin/env python3

import sys
import logging

from random import random
from bisect import bisect_left
from collections import defaultdict

from argparse import ArgumentParser


def argparser():
    ap = ArgumentParser()
    ap.add_argument(
        '--lines',
        default=1000,
        type=int,
        help='number of lines of text to generate'
    )
    ap.add_argument(
        '--words-per-line',
        default=1000,
        type=int,
        help='number of words per line to generate'
    )
    ap.add_argument(
        'freqs',
        help='word frequencies'
    )
    return ap


def load_word_freqs(fn):
    word_freq = defaultdict(int)
    with open(fn) as f:
        for ln, line in enumerate(f, start=1):
            line = line.rstrip('\n')
            try:
                freq, words = line.split(None, 1)
            except Exception as e:
                logging.warning(f'failed to parse line {ln} in {fn}: {e}')
                continue
            for word in words.split():
                word_freq[word] += int(freq)
    return word_freq


def make_frequency_table(word_freqs):
    freq_word = sorted([(v, k) for k, v in word_freqs.items()], reverse=True)
    total = sum(word_freqs.values())
    freqs, words, cumulative = [], [], 0
    for freq, word in freq_word:
        cumulative += freq
        freqs.append(cumulative/total)
        words.append(word)
    return freqs, words


def main(argv):
    args = argparser().parse_args(argv[1:])

    word_freq = load_word_freqs(args.freqs)
    freqs, words = make_frequency_table(word_freq)

    def sample_word():
        return words[bisect_left(freqs, random())]

    for line in range(args.lines):
        text = ' '.join([sample_word() for i in range(args.words_per_line)])
        text = ' '.join(text.split())    # normalize space
        print(text)


if __name__ == '__main__':
    sys.exit(main(sys.argv))
