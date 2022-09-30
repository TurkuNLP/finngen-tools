#!/usr/bin/env python3

import sys
import os
import re
import json
import logging

import chardet

from statistics import median
from argparse import ArgumentParser


def argparser():
    ap = ArgumentParser()
    ap.add_argument('text', nargs='+')
    return ap


def initial_space_count(string):
    for i in range(len(string)):
        if not string[i].isspace():
            return i
    return len(string)


def first_word(line):
    try:
        return line.split()[0]
    except IndexError:
        return ''


def join_paragraph_lines(lines):
    # Paragraphs of continuous text are split into lines no longer
    # than ~70 characters in the corpus. These should be joined into a
    # single line to avoid spurious linebreaks. By contrast,
    # consecutive lines representing e.g. lists, TOCs, or poetry
    # should not be joined. This implements a simple heuristic that
    # appears to mostly differentiate between the two.

    if len(lines) < 2:
        return lines

    # Determine line lengths together with the first word on the
    # following lines
    lengths = []
    for i in range(len(lines)-1):
        lengths.append(len(lines[i].rstrip() + ' ' + first_word(lines[i+1])))

    # Heuristic for "likely regular paragraph"
    if median(lengths) > 65:
        lines = [' '.join(lines)]

    return lines


def normalize_paragraph_space(text):
    lines = text.split('\n')

    # join lines on regular paragraphs
    lines = join_paragraph_lines(lines)

    # if the whole paragraph is indented, slice off indent
    indent = min(initial_space_count(l) for l in lines)
    lines = [l[indent:] for l in lines]

    # remove trailing whitespace, limit number of consecutive spaces
    lines = [l.rstrip() for l in lines]
    lines = [re.sub(r'\s{2,}', '  ', l) for l in lines]

    return '\n'.join(lines)


def normalize_space(text):
    text = text.replace('\r\n', '\n')    # CRLF -> LF

    paragraphs = text.split('\n\n')
    paragraphs = [p.strip('\n') for p in paragraphs]
    paragraphs = [normalize_paragraph_space(p) for p in paragraphs]
    paragraphs = [p for p in paragraphs if p and not p.isspace()]
    return paragraphs


def is_license_text(text):
    text = ' '.join(text.split())
    return any(s in text for s in (
        'public domain',
        'tekijänoikeuksista vapaa',
    ))


def is_produced_by(text):
    text = ' '.join(text.split())
    return any(s in text for s in(
        'Tämän e-kirjan on tuottanut',
        'Tämän e-kirjan ovat tuottaneet',
        'Tämän digikirjan ovat tuottaneet',
        'Tämän sähkökirjan ovat tuottaneet',
        'Denna e-bok har producerats av',
    ))


def split_metadata(paragraphs):
    # Separate initial license text and information on who produced
    # the document, if any
    license_text, produced_by = None, None
    if is_license_text(paragraphs[0]):
        license_text, paragraphs = paragraphs[0], paragraphs[1:]
    if is_produced_by(paragraphs[0]):
        produced_by, paragraphs = paragraphs[0], paragraphs[1:]
    return license_text, produced_by, paragraphs


def decode(binary, name):
    # Use chardet because the original text files have varying
    # encodings and fallback because chardet isn't perfect
    detected = chardet.detect(binary)

    candidates = [
        detected['encoding'],
        'ISO-8859-1',
    ]

    for encoding in candidates:
        try:
            return binary.decode(encoding)
        except Exception as e:
            logging.warning(f'failed to decode {name} as {encoding}: {e}')

    raise UnicodeDecodeError('failed to decode {name}')


def convert_lonnrot(fn, args):
    with open(fn, 'rb') as f:
        binary = f.read()

    text = decode(binary, fn)

    paragraphs = normalize_space(text)

    license_text, produced_by, paragraphs = split_metadata(paragraphs)

    text = '\n\n'.join(paragraphs)

    data = {
        'id': 'lonnrot:' + os.path.splitext(os.path.basename(fn))[0],
        'text': text,
        'meta': {},
    }
    if license_text:
        data['meta']['license'] = license_text
    if produced_by:
        data['meta']['produced_by'] = produced_by

    print(json.dumps(data, ensure_ascii=False))


def main(argv):
    args = argparser().parse_args(argv[1:])

    for fn in args.text:
        convert_lonnrot(fn, args)


if __name__ == '__main__':
    sys.exit(main(sys.argv))
