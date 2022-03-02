#!/usr/bin/env python3

# Extract text from CoNLL-U variant used in the Finnish parsebank

import sys
import gzip

from argparse import ArgumentParser


TEXT_LINE_START = '# text = '


def argparser():
    ap = ArgumentParser()
    ap.add_argument('conllu', nargs='+')
    return ap


def is_text_line(line):
    return line.startswith(TEXT_LINE_START)


def is_para_start_line(line):
    return line.startswith('# <p>') or line.startswith('# <p ')


def is_doc_end_line(line):
    return line.startswith('# </doc>')


def output_document(paragraphs):
    paragraphs = [' '.join(s) for s in paragraphs if s]
    print('\n\n'.join(paragraphs))


def print_parsebank_stream_text(f, args):
    paragraphs = []
    for ln, line in enumerate(f, start=1):
        line = line.rstrip('\n')
        if is_para_start_line(line):
            paragraphs.append([])
        elif is_doc_end_line(line):
            if paragraphs:
                output_document(paragraphs)
            paragraphs = []
            paragraphs
        elif is_text_line(line):
            text = line[len(TEXT_LINE_START):]
            paragraphs[-1].append(text)


def print_parsebank_text(fn, args):
    if fn.endswith('.gz'):
        with gzip.open(fn, 'rt', encoding='utf-8') as f:
            print_parsebank_stream_text(f, args)
    else:
        with open(fn) as f:
            print_parsebank_stream_text(f, args)


def main(argv):
    args = argparser().parse_args(argv[1:])

    for fn in args.conllu:
        print_parsebank_text(fn, args)


if __name__ == '__main__':
    sys.exit(main(sys.argv))

