#!/usr/bin/env python3

# Convert the JSON format in which the Yle corpus
# (http://urn.fi/urn:nbn:fi:lb-2017070501 and three others) is distributed
# into a simple JSONL format with keys 'id', 'text', and 'meta'.

import sys
import os
import re
import json
import logging

from glob import glob
from argparse import ArgumentParser

from bs4 import BeautifulSoup
from markdown import markdown


IGNORED_CONTENT_TYPES = {
    'image',
    'image-pair',
    'slideshow',
    'gallery',
    'infogram',
    'video',
    'audio',
    'youtube-video',
    'facebook-video',
    'vimeo-video',
    'elava-arkisto-video',
    'livefeed',
    'timeline',
    'some-posting',    # twitter, instagram, etc.
    'flockler',    # social media content
    'quote',    # pull quotes, not part of primary text flow
    'table',    # tabular data
    'interactive-table',
    'tehtava-exam',    # interactive content
    'tehtava-assignment',    # interactive content
    'tehtava-carousel',    # interactive content
    'survey',    # interactive content
    'external-content',    # cannot be rendered as text from local data
    'links',    # roughly "related articles"
    'undefined',    # ???
}


BULLET_POINT = '•'


def argparser():
    ap = ArgumentParser()
    ap.add_argument('input', metavar='FILE-OR-DIR')
    return ap


def normalize_paragraph_space(text):
    return '\n'.join(' '.join(l.split()) for l in text.split('\n')).strip()


def normalize_space(text):
    paragraphs = re.split(r'\n(\s+\n|\n)+', text)
    paragraphs = [normalize_paragraph_space(p) for p in paragraphs]
    paragraphs = [p for p in paragraphs if p]
    return '\n\n'.join(paragraphs)


def markdown_to_text(md):
    html = markdown(md)
    soup = BeautifulSoup(html, 'html.parser')
    return soup.get_text()


def render_text(text, args):
    text = markdown_to_text(text)
    return normalize_space(text)


def render_bullet_list(content, args):
    texts = []
    for text in content['items']:
        texts.append(BULLET_POINT + ' ' + render_text(text, args))
    return '\n'.join(texts)


def render_numbered_list(content, args):
    texts = []
    for i, text in enumerate(content['items'], start=1):
        texts.append(f'{i}. ' + render_text(text, args))
    return '\n'.join(texts)


def render_top_list(content, args):
    # "top-list" contains documents, render recursively
    texts = []
    for document in content['items']:
        texts.extend(convert_document(document, args))
    return '\n\n'.join(texts)


def render_aside(content, args):
    # "aside" is a document, render recursively
    texts = convert_document(content, args)
    return '\n\n'.join(texts)


def render_feature(content, args):
    # "feature" contains documents, render recursively
    texts = []
    for document in content['pages']:
        texts.extend(convert_document(document, args))
    return '\n\n'.join(texts)


def convert_document(document, args):
    texts = []
    for content in document['content']:
        type_ = content['type']
        try:
            if type_ in { 'heading', 'text', 'highlight' }:
                texts.append(render_text(content['text'], args))
            elif type_ == 'bullet-list':
                texts.append(render_bullet_list(content, args))
            elif type_ == 'numbered-list':
                texts.append(render_numbered_list(content, args))
            elif type_ == 'top-list':
                texts.append(render_top_list(content, args))
            elif type_ == 'aside':
                texts.append(render_aside(content, args))
            elif type_ == 'feature':
                texts.append(render_feature(content, args))
            elif type_ in IGNORED_CONTENT_TYPES:
                pass
            else:
                logging.warning(f'ignoring content of type {content["type"]}')
        except:
            logging.error(f'failed to convert: {content}')
            pass
    return texts


def convert_yle_json(fn, data, args):
    for document in data['data']:
        id_ = document['id']
        url = document['url']['full']

        meta = {
            'url': url,
            'language': document['language'],
        }

        texts = convert_document(document, args)
            
        # join text elements with an empty line in between.
        text = '\n\n'.join(texts)

        converted = {
            'id': f'ylenews:{id_}',
            'meta': meta,
            'text': text
        }
        print(json.dumps(converted, sort_keys=True, ensure_ascii=False))


def convert_file(fn, args):
    with open(fn) as f:
        data = json.load(f)    
    return convert_yle_json(fn, data, args)


def main(argv):
    args = argparser().parse_args(argv[1:])

    if os.path.isfile(args.input):
        convert_file(args.input, args)
    else:
        paths = glob(f'{args.input}/**/*.json', recursive=True)
        for p in sorted(paths):
            try:
                convert_file(p, args)
            except Exception as e:
                logging.error(f'failed to convert {p}: {e}')
                raise


if __name__ == '__main__':
    sys.exit(main(sys.argv))
