#!/usr/bin/env python3

# Convert the XML format in which the STT corpus
# (http://urn.fi/urn:nbn:fi:lb-2019041501) is distributed into a
# simple JSONL format with keys 'td', 'text', and 'meta'.

import sys
import os
import re
import json
import unicodedata
import logging
import xml.etree.ElementTree as ET

import inscriptis    # HTML to readable text
import bs4    # HTML to text fallback

from collections import defaultdict
from glob import glob
from argparse import ArgumentParser


# XML tags to process
HEADING_TAGS = ('h1', 'h2', 'h3')
PARAGRAPH_TAG = 'p'


# Regex for likely HTML content
LIKELY_HTML_RE = re.compile(r'<[/?]?[a-zA-Z0-9]|&[a-zA-Z0-9#]+;')


def argparser():
    ap = ArgumentParser()
    ap.add_argument(
        '--unicode-norm',
        choices=['NFC', 'NFKC', 'NFD', 'NFKD', 'None'],
        default='NFKC',
        help='unicode normalization to apply',
    )
    ap.add_argument(
        '--no-space-norm',
        default=False,
        action='store_true',
        help='no whitespace normalization'
    )
    ap.add_argument(
        '--no-headline',
        action='store_true',
        help='do not add headlines to text'
    )
    ap.add_argument(
        '--no-html-processing',
        action='store_true',
        help='do not process HTML content to text'
    )
    ap.add_argument('input', metavar='FILE-OR-DIR')
    return ap


def normalize_space(string):
    return ' '.join(string.split())


def normalize_html_space(string):
    # Less aggressive space normalization for text generated from HTML.
    string = string.strip()
    string = re.sub(r'\n\n\n+', '\n\n', string)
    string = '\n'.join(l.strip() for l in string.splitlines())
    return string


def normalize_unicode(string, args):
    return unicodedata.normalize(args.unicode_norm, string)


def normalize_text(string, args):
    if args.unicode_norm != 'None':
        string = normalize_unicode(string, args)
    if not args.no_space_norm:
        string = normalize_space(string)
    return string


def normalize_html_text(string, args):
    if args.unicode_norm != 'None':
        string = normalize_unicode(string, args)
    if not args.no_space_norm:
        string = normalize_html_space(string)
    return string


def remove_namespaces(tree):
    for e in tree.iter():
        e.tag = re.sub(r'^{.*?}', '', e.tag)


def subtree_text(elem):
    return ET.tostring(elem, method='text', encoding='unicode')


def html_to_text(html):
    try:
        return inscriptis.get_text(html).strip()
    except Exception as e:
        logging.warning(f'inscriptis error, falling back to bs4: {e}')
        return bs4.BeautifulSoup(html).get_text().strip()


def has_html(content):
    # rough heuristics for whether HTML processing may be needed
    if any(s in content for s in ('<!--', '-->')):
        return True    # comments
    elif not all(c in content for c in '<>') and not '&' in content:
        return False    # shortcuts most cases
    elif LIKELY_HTML_RE.search(content):
        return True
    else:
        return False


def get_clean_text(content, args):
    if args.no_html_processing or not has_html(content):
        return normalize_text(content, args)
    else:
        text = html_to_text(content)
        return normalize_html_text(text, args)


def parse_contentmeta(elem):
    values = defaultdict(list)
    for e in elem:
        value = normalize_space(subtree_text(e))
        if value:
            values[e.tag].append(value)

    # replace lists with single items with that item
    values = { k: v[0] if len(v) == 1 else v for k, v in values.items() }

    return values


def only_child_with_tag(elem, tag):
    children = list(elem)
    assert len(children) == 1 and children[0].tag == tag
    return children[0]


def get_contentset_text(elem, args):
    # Drop wrapping <inlineXML>, <html>, and <body> elements
    elem = only_child_with_tag(elem, 'inlineXML')
    elem = only_child_with_tag(elem, 'html')
    elem = only_child_with_tag(elem, 'body')

    paragraphs = []
    for e in elem:
        if e.tag in HEADING_TAGS or e.tag == PARAGRAPH_TAG:
            content = subtree_text(e)
            text = get_clean_text(content, args)
            paragraphs.append(text)
        else:
            logging.warning(f'unexpected tag {e.tag}')

    paragraphs = [p for p in paragraphs if p]
    return '\n\n'.join(paragraphs)


def convert_file(path, args):
    text, contentmeta = None, None

    tree = ET.parse(path)
    remove_namespaces(tree)

    root = tree.getroot()
    id_ = root.attrib['guid']
    for e in root:
        if e.tag ==  'contentSet':
            assert text is None
            text = get_contentset_text(e, args)
        elif e.tag == 'contentMeta':
            assert contentmeta is None
            contentmeta = parse_contentmeta(e)
        elif e.tag == 'itemMeta':
            pass    # little additional information to contentMeta
        elif e.tag == 'catalogRef':
            pass    # redundant, all files have the same refs
        elif e.tag == 'assert':
            pass    # rare, unused
        else:
            logging.warning(f'unexpected tag {e.tag}')

    if not args.no_headline:
        if 'headline' in contentmeta:
            text = contentmeta['headline'] + '\n\n' + text

    data = {
        'id': id_,
        'meta': { 'sourcemeta': contentmeta },
        'text': text,        
    }
    print(json.dumps(data, ensure_ascii=False))
    
    
def main(argv):
    args = argparser().parse_args(argv[1:])

    if os.path.isfile(args.input):
        convert_file(args.input, args)
    else:
        paths = glob(f'{args.input}/**/*.xml', recursive=True)
        for p in paths:
            convert_file(p, args)


if __name__ == '__main__':
    sys.exit(main(sys.argv))
