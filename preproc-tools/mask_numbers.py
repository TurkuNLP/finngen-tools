#!/usr/bin/env python3

# High recall, low precision number masking for potential PII. Known
# unnecessarily masked identifiers include ISBNs, ISSNs, and PMIDs as
# well as large monetary and other values.

import sys
import regex

from argparse import ArgumentParser


NUMBER_START_RE = regex.compile(r'\b[[:digit:]]')

NUMBER_RE = regex.compile(r'^(?:[[:digit:]][[:space:]().+–—-]*){6,12}[[:digit:]]\b')

YEAR_RE = r'(?:20[[:digit:]]{2}|1[0-9][[:digit:]]{2}|[[:digit:]]{2})'
MONTH_RE = r'[01]?[[:digit:]]'
DAY_RE = r'[0-3]?[[:digit:]]'
DATE_SEP = r'\s*[.–—-]\s*'

DATE_RE_DMY = regex.compile(DAY_RE+DATE_SEP+MONTH_RE+DATE_SEP+YEAR_RE+r'\b')
DATE_RE_YMD = regex.compile(YEAR_RE+DATE_SEP+MONTH_RE+DATE_SEP+DAY_RE+r'\b')
DATE_RE_YDM = regex.compile(YEAR_RE+DATE_SEP+DAY_RE+DATE_SEP+MONTH_RE+r'\b')

YEAR_RANGE_RE = regex.compile(r'^(?:1[0-9][[:digit:]]{2}|20[[:digit:]]{2})\s*[.–—-]\s*(?:1[0-9][[:digit:]]{2}|20[[:digit:]]{2})\b')


def argparser():
    ap = ArgumentParser()
    ap.add_argument('text', nargs='+')
    return ap


def mask_number(string, num_leading=2, replace_char='0'):
    masked, digit_count = '', 0
    for c in string:
        if not c.isdigit():
            masked += c
        else:
            if digit_count >= num_leading:
                masked += replace_char
            else:
                masked += c
            digit_count += 1
    return masked


def keep_span_length(string):
    length = None
    for RE in (DATE_RE_DMY, DATE_RE_YMD, DATE_RE_YDM, YEAR_RANGE_RE):
        m = RE.match(string)
        if not m:
            continue
        if length is None or m.end() > length:
            length = m.end()
    if length is None:
        return None
    return length


def mask_numbers(string):
    # Mask any number that is potentially PII.
    num_spans, keep_spans = [], []
    for m1 in NUMBER_START_RE.finditer(string):
        keep_length = keep_span_length(string[m1.start():])
        if keep_length is not None:
            keep_spans.append((m1.start(), m1.start()+keep_length))
            continue
        m2 = NUMBER_RE.match(string[m1.start():])
        if m2:
            num_spans.append((m1.start(), m1.start()+m2.end()))

    def overlap(s1, s2):
        return s1[0] < s2[1] and s1[1] > s2[0]

    num_spans = [
        ns for ns in num_spans
        if not any(overlap(ns, ks) for ks in keep_spans)
    ]

    for start, end in num_spans:
        before, num, after = string[:start], string[start:end], string[end:]
        string = before + mask_number(num) + after

    return string


def main(argv):
    args = argparser().parse_args(argv[1:])

    for fn in args.text:
        with open(fn) as f:
            for l in f:
                print(mask_numbers(l), end='')


if __name__ == '__main__':
    sys.exit(main(sys.argv))
