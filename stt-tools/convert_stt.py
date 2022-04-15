#!/usr/bin/env python3

# Convert the XML format in which the STT corpus
# (http://urn.fi/urn:nbn:fi:lb-2019041501) is distributed into a
# simple JSONL format with keys 'id', 'text', and 'meta'.

import sys
import os
import re
import json
import unicodedata
import logging
import xml.etree.ElementTree as ET

import inscriptis    # HTML to readable text
import bs4    # HTML to text fallback
import ftfy

from string import punctuation
from collections import defaultdict
from glob import glob
from argparse import ArgumentParser

# XML tags to process
HEADING_TAGS = ('h1', 'h2', 'h3')
PARAGRAPH_TAG = 'p'

# Regexes for various parts of the document
LIKELY_HTML_RE = re.compile(r'<[/?]?[a-zA-Z0-9]|&[a-zA-Z0-9#]+;')
TAG_LINE_RE = re.compile(r'^[a-zäöå0-9, -]+$')
AUTHOR_RE = re.compile(r'^\s*([/-]+\s*)?[a-zäöåA-ZÄÖÅ]\S*\s*$')

# Common author lines
KNOWN_AUTHORS = {
    '-jv', '-mal', '-ns', '-nt', '-po', '-ps', '-psi', 'ah', 'aih', 'aj', 'am',
    'anma', 'anna', 'at', 'au', 'ek', 'elko', 'elr', 'en', 'eska', 'ev', 'ha',
    'hek', 'hesi', 'hk', 'hku', 'hl', 'ht', 'hv', 'hw', 'jali', 'jas', 'jaso',
    'jek', 'jh', 'jk', 'joyl', 'js', 'jtv', 'juan', 'juse', 'juvu', 'jvr', 'kh',
    'ki', 'kife', 'kl', 'kmi', 'kp', 'ks', 'ksy', 'kv', 'la', 'lak', 'lefa',
    'lf', 'lk', 'ls', 'mam', 'me', 'mh', 'mi', 'mk', 'mm', 'mmr', 'mp', 'mpy',
    'mr', 'msi', 'msv', 'muks', 'mv', 'må', 'ns', 'oak', 'ok', 'ola', 'op',
    'pemo', 'pepo', 'pf', 'pir', 'pjm', 'pk', 'pka', 'pks', 'pls', 'pn', 'ppa',
    'pph', 'pr', 'ps', 'psk', 'ptp', 'ral', 'rami', 'rana', 'rera', 'rila',
    'rj', 'rm', 'rmk', 'ros-' 'rs', 'rt', 'sa', 'sani', 'sato', 'sepe', 'sm',
    'sn', 'sss', 'sv', 'th', 'tjm', 'tk', 'tl', 'tm', 'tn', 'tomi', 'ts', 'tw',
    'uj/uj', 'ull', 'umh', 'uo', 'voa',
}


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


def normalize_line_space(string):
    # Space normalization that preserves line breaks within paragraphs
    string = string.strip()
    string = re.sub(r'\n\n\n+', '\n\n', string)
    string = '\n'.join(' '.join(l.split()) for l in string.splitlines())
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
        string = normalize_line_space(string)
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
        logging.warning(f'inscriptis error, falling back to bs4: {e}: "{html}"')
        return bs4.BeautifulSoup(html, 'lxml').get_text().strip()


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


def get_normalized_paragraphs(content, args):
    if args.no_html_processing or not has_html(content):
        paragraphs = [p for p in re.split(r'\n\n+', content) if p]
        return [normalize_text(p, args) for p in paragraphs]
    else:
        text = html_to_text(content)
        text = normalize_html_text(text, args)
        return [p for p in re.split(r'\n\n+', text) if p]


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


def remove_tag_lines(paragraphs):
    while paragraphs:
        if paragraphs[0] and not TAG_LINE_RE.match(paragraphs[0]):
            break
        paragraphs = paragraphs[1:]
    return paragraphs


def remove_author_lines(paragraphs):
    while paragraphs:
        if paragraphs[-1] and not AUTHOR_RE.match(paragraphs[-1]):
            break
        paragraphs = paragraphs[:-1]
    paragraphs = [p for p in paragraphs if not p.strip() in KNOWN_AUTHORS]
    return paragraphs


def remove_paragraph_comments(paragraph):
    # Comments typically delimited by two or more slashes
    if '//' not in paragraph:
        return paragraph    # fast, most paragraphs

    # By far the most prominent set of exceptions are "http://" and
    # similar; temporarily escape these to avoid interpreting them
    # as comments
    ESCAPE = '[[DOUBLESLASH]]'
    assert ESCAPE not in paragraph
    paragraph = re.sub(r'((:?https?|ftp):)//', r'\1'+ESCAPE, paragraph,
                       flags=re.IGNORECASE)

    # Remove comments
    paragraph = re.sub(r'//+.*//+', ' ', paragraph)

    # Renormalize space
    paragraph = '\n'.join(' '.join(l.split()) for l in paragraph.splitlines())

    # If comment markers remain in a reasonably short paragraph, drop
    # the whole paragraph
    if '//' in paragraph and len(paragraph) < 80:
        paragraph = ''

    # Unescape
    paragraph = paragraph.replace(ESCAPE, '//')
    return paragraph


def remove_comments(paragraphs):
    return [remove_paragraph_comments(p) for p in paragraphs]


def remove_paragraph_inserts(paragraph):
    if not any(s in paragraph for s in ('*', '---', '___', '===')):
        return paragraph

    # Remove inserts such as "***** TIEDOTE*TIEDOTE*TIEDOTE *****"
    paragraph = re.sub(r'\*{3}[A-ZÅÄÖ0-9 *-]*$', ' ', paragraph)
    paragraph = re.sub(r'\*{3}.*?\*{3,}', ' ', paragraph)

    # Drop remaining "*TIEDOTE*TIEDOTE*TIEDOTE*" and similar
    if paragraph.strip().startswith('*') and 'TIEDOTE' in paragraph:
        paragraph = ''
    elif paragraph.strip().startswith('***') and len(paragraph) < 60:
        paragraph = ''

    # Reduce inserts such as "----------------------"
    for s in ('***', '---', '___', '==='):
        paragraph = re.sub(re.escape(s)+r'+', s, paragraph)

    return paragraph


def remove_inserts(paragraphs):
    return [remove_paragraph_inserts(p) for p in paragraphs]


def remove_paragraph_creditline(paragraph):
    if '(STT' not in paragraph:
        return paragraph
    paragraph = re.sub(r'\(STT[^)]*?\)([!?.,])', r'\1', paragraph)
    paragraph = re.sub(r'\(STT[^)]*?\)[a-zäöå /-]*$', '', paragraph)
    paragraph = '\n'.join(' '.join(l.split()) for l in paragraph.splitlines())
    return paragraph


def remove_creditline(paragraphs):
    return [remove_paragraph_creditline(p) for p in paragraphs]


def remove_punct_only(paragraphs):
    return [
        p for p in paragraphs
        if not all(c in punctuation or c.isspace() for c in p)
    ]


def fix_texts(paragraphs):
    return [
        normalize_line_space(ftfy.fix_text(p))
        for p in paragraphs
    ]


def clean_paragraphs(paragraphs, args):
    # Remove tags, comments, and other non-prose material from paragraphs.
    # For example, for the input
    # [
    #     "puolueet",
    #     "kiinan puoluekokous",
    #     "///jatkettu versio///",
    #     "Kahdeksan voimahahmoa jättämässä puolueen johtopaikat Kiinassa
    #      Peking, 16. 10. (STT—Reuter—TT—AFP)"
    # ]
    # the function will return
    # [
    #     "Kahdeksan voimahahmoa jättämässä puolueen johtopaikat Kiinassa
    #      Peking, 16. 10."
    # ]
    paragraphs = remove_comments(paragraphs)
    paragraphs = remove_inserts(paragraphs)
    paragraphs = remove_tag_lines(paragraphs)
    paragraphs = remove_author_lines(paragraphs)
    paragraphs = remove_creditline(paragraphs)
    paragraphs = remove_punct_only(paragraphs)
    paragraphs = fix_texts(paragraphs)
    paragraphs = [p for p in paragraphs if p and not p.isspace()]
    return paragraphs


def has_sentence_ending_punctuation(string):
    return string and string.rstrip()[-1] in '.:!?'


def potential_partial_heading_start(string):
    return (
        string and
        (string[0].isupper() or string[0].isdigit()) and
        len(string) < 50 and
        not has_sentence_ending_punctuation(string)
    )


def likely_partial_heading_end(string):
    return (
        string and
        string[0].islower() and
        len(string) < 50 and
        not has_sentence_ending_punctuation(string)
    )


def join_split_headings(paragraphs):
    # Headings are split across paragraphs in some documents; rejoin
    # heuristically. (Mostly happens in pre-2000 papers.)
    i = 1
    while i < len(paragraphs):
        if (likely_partial_heading_end(paragraphs[i]) and
            potential_partial_heading_start(paragraphs[i-1])):
            paragraphs[i-1] = paragraphs[i-1] + ' ' + paragraphs[i]
            paragraphs = paragraphs[:i] + paragraphs[i+1:]
        else:
            i += 1
    return paragraphs


def get_contentset_text(elem, args):
    # Drop wrapping <inlineXML>, <html>, and <body> elements
    elem = only_child_with_tag(elem, 'inlineXML')
    elem = only_child_with_tag(elem, 'html')
    elem = only_child_with_tag(elem, 'body')

    paragraphs = []
    for e in elem:
        if e.tag in HEADING_TAGS or e.tag == PARAGRAPH_TAG:
            content = subtree_text(e)
            paragraphs.extend(get_normalized_paragraphs(content, args))
        else:
            logging.warning(f'unexpected tag {e.tag}')

    paragraphs = clean_paragraphs(paragraphs, args)
    paragraphs = join_split_headings(paragraphs)

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
        for p in sorted(paths):
            try:
                convert_file(p, args)
            except Exception as e:
                logging.error(f'failed to convert {p}: {e}')
                raise


if __name__ == '__main__':
    sys.exit(main(sys.argv))
