#!/usr/bin/env python3

# Convert the CoNLL-U format in which the Finnish parsebank
# (https://turkunlp.org/finnish_nlp.html#parsebank) is distributed into a
# simple JSONL format with keys 'id', 'text', and 'meta'.

import sys
import gzip
import json
import xml.etree.ElementTree as ET

from argparse import ArgumentParser


# Start of lines with document perplexity values
DELEX_PPL_LINE_START = '# delex_lm_mean_perplexity: '
LEX_PPL_LINE_START = '# lex_lm_mean_perplexity: '

# Start of lines with predicted register
REGISTER_LINE_START = '# predicted register: '

# Start of lines with document text
TEXT_LINE_START = '# text = '


def argparser():
    ap = ArgumentParser()
    ap.add_argument('conllu', nargs='+')
    return ap


def is_text_line(line):
    return line.startswith(TEXT_LINE_START)


def is_para_start_line(line):
    return line.startswith('# <p>') or line.startswith('# <p ')


def is_doc_start_line(line):
    return line.startswith('# <doc ')


def is_doc_end_line(line):
    return line.startswith('# </doc>')


def doc_attributes(line):
    assert is_doc_start_line(line)
    assert line.endswith('>')
    elem = ET.fromstring(line[2:] + '</doc>')
    return elem.attrib


def rest_of_line_starting_with(lines, start):
    for line in lines:
        if line.startswith(start):
            return line[len(start):]
    return None


def get_paragraphs(lines):
    paragraphs = None
    for line in lines:
        line = line.rstrip('\n')
        if is_doc_start_line(line):
            assert paragraphs is None
            paragraphs = []
        elif is_para_start_line(line):
            paragraphs.append([])
        elif is_text_line(line):
            text = line[len(TEXT_LINE_START):]
            paragraphs[-1].append(text)
    paragraphs = [' '.join(s) for s in paragraphs if s]
    return paragraphs


def output_document(lines, args):
    delex_ppl = float(rest_of_line_starting_with(lines, DELEX_PPL_LINE_START))
    lex_ppl = float(rest_of_line_starting_with(lines, LEX_PPL_LINE_START))
    register = rest_of_line_starting_with(lines, REGISTER_LINE_START)

    attrib = doc_attributes(lines[0])    # assume first is <doc> line
    attrib.update({
        'delex_lm_mean_perplexity': delex_ppl,
        'lex_lm_mean_perplexity': lex_ppl,
        'predicted register': register,
    })

    text = '\n\n'.join(get_paragraphs(lines))
    data = {
        'id': attrib.pop('id'),
        'text': text,
        'meta': attrib,
    }
    print(json.dumps(data, ensure_ascii=False))


def convert_parsebank_stream(f, args):
    current_lines = []
    for ln, line in enumerate(f, start=1):
        line = line.rstrip('\n')
        if is_doc_start_line(line):
            if current_lines:
                output_document(current_lines, args)
            current_lines = []
        current_lines.append(line)
    if current_lines:
        output_document(current_lines, args)


def convert_parsebank(fn, args):
    if fn.endswith('.gz'):
        with gzip.open(fn, 'rt', encoding='utf-8') as f:
            convert_parsebank_stream(f, args)
    else:
        with open(fn) as f:
            convert_parsebank_stream(f, args)


def main(argv):
    args = argparser().parse_args(argv[1:])

    for fn in args.conllu:
        convert_parsebank(fn, args)


if __name__ == '__main__':
    sys.exit(main(sys.argv))
