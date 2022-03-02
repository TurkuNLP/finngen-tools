#!/usr/bin/env python3

# Filter the CoNLL-U variant used in the Finnish parsebank

import sys
import gzip

from argparse import ArgumentParser


# Predicted registers to filter out
FILTERED_REGISTERS = {
    'machine translated'
}

# Start of lines with document perplexity values
DELEX_PPL_LINE_START = '# delex_lm_mean_perplexity: '
LEX_PPL_LINE_START = '# lex_lm_mean_perplexity: '

# Start of lines with predicted register
REGISTER_LINE_START = '# predicted register: '


def argparser():
    ap = ArgumentParser()
    ap.add_argument(
        '--max-ppl',
        default=None,
        type=float
    )
    ap.add_argument(
        '--max-delex-ppl',
        default=None,
        type=float
    )
    ap.add_argument(
        '-v',
        '--invert',
        default=False,
        action='store_true'
    )
    ap.add_argument('conllu', nargs='+')
    return ap


def is_doc_start_line(line):
    return line.startswith('# <doc')


def rest_of_line_starting_with(lines, start):
    for line in lines:
        if line.startswith(start):
            return line[len(start):]
    return None


def filter_document(lines, args):
    delex_ppl = float(rest_of_line_starting_with(lines, DELEX_PPL_LINE_START))
    lex_ppl = float(rest_of_line_starting_with(lines, LEX_PPL_LINE_START))
    register = rest_of_line_starting_with(lines, REGISTER_LINE_START)

    if register in FILTERED_REGISTERS:
        return True
    elif args.max_ppl is not None and lex_ppl > args.max_ppl:
        return True
    elif args.max_delex_ppl is not None and delex_ppl > args.max_delex_ppl:
        return True


def process_document(lines, args):
    skip = filter_document(lines, args)

    if args.invert:
        skip = not skip

    if skip:
        return None
    else:
        for line in lines:
            print(line)


def filter_parsebank_stream(f, args):
    current_lines = []
    for ln, line in enumerate(f, start=1):
        line = line.rstrip('\n')
        if is_doc_start_line(line):
            if current_lines:
                process_document(current_lines, args)
            current_lines = []
        current_lines.append(line)


def filter_parsebank(fn, args):
    if fn.endswith('.gz'):
        with gzip.open(fn, 'rt', encoding='utf-8') as f:
            filter_parsebank_stream(f, args)
    else:
        with open(fn) as f:
            filter_parsebank_stream(f, args)


def main(argv):
    args = argparser().parse_args(argv[1:])

    for fn in args.conllu:
        filter_parsebank(fn, args)


if __name__ == '__main__':
    sys.exit(main(sys.argv))
