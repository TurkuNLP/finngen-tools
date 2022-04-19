#!/usr/bin/env python3

# Convert the VRT format used in the Suomi24 corpus distribution
# (http://urn.fi/urn:nbn:fi:lb-2017021506) to text and other formats.

import sys
import re
import json
import logging
import xml.etree.ElementTree as ET

from hashlib import md5
from collections import namedtuple
from argparse import ArgumentParser


Word = namedtuple('Word', 'word ref lemma lemmacomp pos msd dephead deprel spaces initid lex')


def argparser():
    ap = ArgumentParser()
    ap.add_argument('--include-quoted', default=False, action='store_true') 
    ap.add_argument('--jsonl', default=False, action='store_true') 
    ap.add_argument('--tsv', default=False, action='store_true')
    ap.add_argument('file', nargs='+')
    return ap


def is_comment_line(line):
    return line.startswith('<!-- ')


def is_text_start_line(line):
    return line.startswith('<text ')


def is_text_end_line(line):
    return line.startswith('</text>')


def parse_text_line(line):
    line = line.rstrip()
    return ET.fromstring(f'{line}</text>')


def is_paragraph_start_line(line):
    return line.startswith('<paragraph ')


def is_paragraph_end_line(line):
    return line.startswith('</paragraph>')


def parse_paragraph_line(line):
    line = line.rstrip()
    return ET.fromstring(f'{line}</paragraph>')
    

def is_sentence_start_line(line):
    return line.startswith('<sentence ')


def is_sentence_end_line(line):
    return line.startswith('</sentence>')


def parse_sentence_line(line):
    line = line.rstrip()
    return ET.fromstring(f'{line}</sentence>')


def make_id(element):
    return md5(ET.tostring(element)).hexdigest()


def parse_attr_value(string):
    attr_value = {}
    for av in string.split('|'):
        if av and av != '_':
            attr, value = av.split('=', 1)
            attr_value[attr] = value
    return attr_value


UNESCAPE_SPACE_MAP = {
    r'\n': '\n',
    r'\t': '\t',
    r'\s': ' ',
    '\u00A0': ' ',    # non-breaking space
    '\u2002': ' ',    # en space
    '\u2003': ' ',    # em space
    '\u2004': ' ',    # three per em space
    '\u2005': ' ',    # four per em space
    '\u2006': ' ',    # six per em space
    '\u2007': ' ',    # figure space
    '\u2008': ' ',    # punctuation space
    '\u2009': ' ',    # thin space
    '\u200A': ' ',    # hairspace
    '\u202F': ' ',    # narrow non-breaking space
    '\u3000': ' ',    # ideographic space
}


def unescape_space(string):
    orig, unescaped = string, []
    while string:
        found = False
        for k, v in UNESCAPE_SPACE_MAP.items():
            if string.startswith(k):
                unescaped.append(v)
                string = string[len(k):]
                found = True
                break
        if not found:
            logging.warning(
                f'failed to unescape space: "{orig}" '
                f'({",".join(repr(c) for c in orig)})')
            break
    return ''.join(unescaped)


def normalize_space(text):
    text = re.sub(r'  +', ' ', text)
    paragraphs = re.split(r'\n\n+', text)
    paragraphs = [p for p in paragraphs if p and not p.isspace()]
    paragraphs = [' '.join(p.split()) for p in paragraphs]
    text = '\n\n'.join(paragraphs)
    return text

    
def unescape_text(text):
    text = text.replace('&lt;', '<')
    text = text.replace('&gt;', '>')
    text = text.replace('&amp;', '&')
    return text


TEXT_BY_COMMENT_ID = {}


def output_text(id_, textelem, strings, options):
    text = ''.join(strings)
    text = normalize_space(text)

    if options.include_quoted:
        # store current
        comment_id = textelem.attrib['comment_id']
        TEXT_BY_COMMENT_ID[comment_id] = text
        quoted_id = textelem.attrib['quoted_comment_id']
        if quoted_id != '0' and quoted_id in TEXT_BY_COMMENT_ID:
            quoted_text = TEXT_BY_COMMENT_ID[quoted_id]
            quoted_lines = quoted_text.split('\n')
            quoted_lines = [f'> {l}' for l in quoted_lines]
            quoted_text = '\n'.join(quoted_lines)
            text = f'{quoted_text}\n\n{text}'
        
    if options.jsonl:
        data = {
            'id': id_,
            'text': text,
            'meta': { 'sourcemeta': textelem.attrib },
        }
        print(json.dumps(data, sort_keys=True, ensure_ascii=False))
    elif not options.tsv:
        print('-' * 20, id_, '-' * 20)
        print(text)
    else:
        encoded = json.dumps(text, ensure_ascii=False)
        print(f'{id_}\t{encoded}')


def vrt_to_text(fn, options):
    id_, textelem, paraelem, sentelem, strings = None, None, None, None, None
    with open(fn) as f:
        for ln, l in enumerate(f, start=1):
            if is_comment_line(l):
                continue
            elif is_text_start_line(l):
                assert textelem is None
                textelem = parse_text_line(l)
                id_ = make_id(textelem)
                strings = []
            elif is_text_end_line(l):
                assert textelem is not None
                output_text(id_, textelem, strings, options)
                id_, textelem, strings = None, None, None
            elif is_paragraph_start_line(l):
                assert paraelem is None
                paraelem = parse_paragraph_line(l)
            elif is_paragraph_end_line(l):
                assert paraelem is not None
                paraelem = None
            elif is_sentence_start_line(l):
                assert sentelem is None
                sentelem = parse_sentence_line(l)
            elif is_sentence_end_line(l):
                assert sentelem is not None
                sentelem = None
            else:
                fields = l.rstrip('\n').split('\t')
                word = Word(*fields)
                spaces = parse_attr_value(word.spaces)
                if 'SpacesBefore' in spaces:
                    strings.append(unescape_space(spaces['SpacesBefore']))
                    del spaces['SpacesBefore']
                strings.append(unescape_text(word.word))
                if 'SpacesInToken' in spaces:
                    del spaces['SpacesInToken']    # redundant
                if not spaces:
                    strings.append(' ')    # single space by default
                elif 'SpacesAfter' in spaces:
                    strings.append(unescape_space(spaces.get('SpacesAfter')))
                else:
                    assert spaces.get('SpaceAfter') == 'No', spaces


def main(argv):
    args = argparser().parse_args(argv[1:])
    for fn in args.file:
        vrt_to_text(fn, args)


if __name__ == '__main__':
    sys.exit(main(sys.argv))
