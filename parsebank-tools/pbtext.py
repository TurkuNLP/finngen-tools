#!/usr/bin/env python3

# Extract text from CoNLL-U variant used in the Finnish parsebank

import sys
import gzip
import json
import xml.etree.ElementTree as ET

from argparse import ArgumentParser


TEXT_LINE_START = '# text = '


def argparser():
    ap = ArgumentParser()
    ap.add_argument('--jsonl', default=False, action='store_true')
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
    assert line.startswith('# <doc ')
    assert line.endswith('>')
    line = line[2:-1] + ' />'
    elem = ET.fromstring(line)
    return elem.attrib


def output_document(doc_start, paragraphs, args):
    paragraphs = [' '.join(s) for s in paragraphs if s]
    text = '\n\n'.join(paragraphs)
    if not args.jsonl:
        print(text)
    else:
        attrib = doc_attributes(doc_start)
        data = {}
        if 'id' in attrib:
            data['id'] = attrib.pop('id')
        else:
            collection, url = attrib.pop('collection'), attrib.pop('url')
            data['id'] = f'{collection}:{url}'
        data['meta'] = attrib
        data['text'] = text
        print(json.dumps(data, ensure_ascii=False))


def print_parsebank_stream_text(f, args):
    doc_start, paragraphs = None, None
    for ln, line in enumerate(f, start=1):
        line = line.rstrip('\n')
        if is_doc_start_line(line):
            assert doc_start is None
            doc_start = line
            paragraphs = []
        elif is_doc_end_line(line):
            if paragraphs:
                output_document(doc_start, paragraphs, args)
            doc_start, paragraphs = None, None
        elif is_para_start_line(line):
            paragraphs.append([])
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

