#!/usr/bin/env python3

# Filter JSONL based on 'text' value using various statistics.
# Based on filterdocs.py from https://github.com/TurkuNLP/deepfin-tools.

import sys
import os
import re
import json
import logging

import gcld3

from string import punctuation
from collections import defaultdict
from argparse import ArgumentParser


# Word regex for e.g. --min-words option
WORD_RE = re.compile(r'\b(?:[A-ZÅÄÖ][a-zåäö]{1,}|[a-zåäö]{2,})\b')

# Short word regex for --short-ratio option
SHORT_WORD_RE = re.compile(r'\b[a-zåäöA-ZÅÄÖ]\b')

# Regex for non-Finnish unicode letter (https://stackoverflow.com/a/6314634)
FOREIGN_LETTER = re.compile(r'[^\W\d_a-zA-ZåäöÅÄÖ]')

PUNCT = set(punctuation)


def argparser():
    ap = ArgumentParser(description='Filter JSONL texts')
    ap.add_argument('-a', '--avg-len', default=None, type=int,
                    help='minimum average paragraph length')
    ap.add_argument('-d', '--digit-ratio', default=None, type=float,
                    help='maximum ratio of digit characters')
    ap.add_argument('-F', '--foreign-ratio', default=None, type=float,
                    help='maximum ratio of non-word alphabetic characters')
    ap.add_argument('-H', '--short-ratio', default=None, type=float,
                    help='maximum ratio of short words')
    ap.add_argument('-l', '--lang-prob', default=None, type=float,
                    help='minimum predicted probability of target language')
    ap.add_argument('-p', '--punct-ratio', default=None, type=float,
                    help='maximum ratio of punctuation characters')
    ap.add_argument('-u', '--upper-ratio', default=None, type=float,
                    help='maximum ratio of uppercase characters')
    ap.add_argument('-w', '--min-words', default=None, type=int,
                    help='minimum number of words')
    ap.add_argument('-v', '--invert', default=False, action='store_true',
                    help='invert filter criteria')
    ap.add_argument('jsonl', nargs='+')
    return ap


def get_words(text):
    return WORD_RE.findall(text)


def get_paragraphs(text):
    return [p for p in re.split(r'\n\n+', text) if p and not p.isspace()]


def get_short_words(text):
    return SHORT_WORD_RE.findall(text)


def num_words(text):
    return len(get_words(text))


def num_paragraphs(text):
    return len(get_paragraphs(text))


def avg_len(text):
    return num_words(text) / num_paragraphs(text)


def digit_ratio(text):
    return sum(c.isdigit() for c in text)/len(text)


def upper_ratio(text):
    return sum(c.isupper() for c in text)/len(text)


def foreign_ratio(text):
    return len(FOREIGN_LETTER.findall(text))/len(text)


def punct_ratio(text):
    return sum(c in PUNCT for c in text)/len(text)


def lang_prob(text, lang='fi'):
    if lang_prob.detector is None:
        lang_prob.detector = gcld3.NNetLanguageIdentifier(0, 1000)
    result = lang_prob.detector.FindLanguage(text)
    if result.language != lang:
        return 0.0
    else:
        return result.probability
lang_prob.detector = None


def short_ratio(text):
    words, short = get_words(text), get_short_words(text)
    if not words and not short:
        return 0.0
    else:
        return len(short)/(len(words)+len(short))


def filter_text(t, args):
    if not t or t.isspace():
        return 'empty'
    if args.avg_len is not None and avg_len(t) < args.avg_len:
        return 'avg-len'
    if args.punct_ratio is not None and punct_ratio(t) > args.punct_ratio:
        return 'punct-ratio'
    if args.upper_ratio is not None and upper_ratio(t) > args.upper_ratio:
        return 'upper-ratio'
    if args.digit_ratio is not None and digit_ratio(t) > args.digit_ratio:
        return 'digit-ratio'
    if args.foreign_ratio is not None and foreign_ratio(t) > args.foreign_ratio:
        return 'foreign-ratio'
    if args.short_ratio is not None and short_ratio(t) > args.short_ratio:
        return 'short-ratio'
    if args.min_words is not None and num_words(t) < args.min_words:
        return 'min-words'
    if args.lang_prob is not None and lang_prob(t) < args.lang_prob:
        return 'lang-prob'
    return None


def filter_document(text, stats, args):
    filter_condition = filter_text(text, args)
    if filter_condition is None:
        result = 'pass-all'
        skip = False
    else:
        result = f'fail-{filter_condition}'
        skip = True
    stats[result] += 1

    if args.invert:
        skip = not skip
    return skip


def report_stats(name, stats, out=sys.stderr):
    stats = stats.copy()
    docs, output = stats.pop('total-docs'), stats.pop('output-docs')
    for k, v in sorted(stats.items()):
        print('{}:\t{}\t{} ({:.1%})'.format(
            name, k, v, v/docs), file=sys.stderr, flush=True)
    print('{}: output {}/{} documents ({:.1%})'.format(
        name, output, docs, output/docs), file=sys.stderr, flush=True)
    pass


def filter_jsonl(fn, args):
    stats = defaultdict(int)
    with open(fn) as f:
        for ln, line in enumerate(f, start=1):
            data = json.loads(line)
            id_, text = data['id'], data['text']
            stats['total-docs'] += 1
            if not filter_document(text, stats, args):
                print(line, end='')
                stats['output-docs'] += 1
    report_stats(os.path.basename(fn), stats)


def main(argv):
    args = argparser().parse_args(argv[1:])

    for fn in args.jsonl:
        filter_jsonl(fn, args)


if __name__ == '__main__':
    sys.exit(main(sys.argv))
