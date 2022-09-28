#!/usr/bin/env python3

# Convert the JSON format in which Reddit data
# (https://files.pushshift.io/reddit/) is distributed
# into a simple JSONL format with keys 'id', 'text', and 'meta'.

import sys
import re
import json
import logging

import inscriptis

from argparse import ArgumentParser

from markdown import markdown


def argparser():
    ap = ArgumentParser()
    ap.add_argument('jsonl', nargs='+')
    return ap


def normalize_paragraph_space(text):
    text = text.strip()
    lines = text.split('\n')
    lines = [re.sub(r'\s{2,}', '  ', l) for l in lines]
    lines = [l.strip() for l in lines]
    text = '\n'.join(lines)
    return text


def normalize_space(text):
    text = text.strip()
    paragraphs = text.split('\n\n')
    paragraphs = [normalize_paragraph_space(p) for p in paragraphs]
    paragraphs = [p for p in paragraphs if p and not p.isspace()]
    text = '\n\n'.join(paragraphs)
    return text


def markdown_to_html(md):
    # Se https://www.reddit.com/wiki/markdown/
    # TODO: consider using https://github.com/reddit/snudown

    md = md.replace('~~', '~')    # ~~strikethrough~~
    md = re.sub(r'&gt;!(.*?)!&lt;', r'\1', md)    # >!spoiler!<
    
    return markdown(md, extensions=['nl2br', 'tables'])


def markdown_to_text(md):
    html = markdown_to_html(md)
    text = inscriptis.get_text(html)
    text = normalize_space(text)
    return text


def convert_reddit(fn, args):
    seen = set()
    dup_count, deleted_count = 0, 0
    with open(fn) as f:
        for ln, line in enumerate(f, start=1):
            data = json.loads(line)

            id_ = data.pop('id')
            if id_ in seen:
                dup_count += 1
                continue
            seen.add(id_)

            body = data.pop('body')
            if body == '[deleted]':
                deleted_count += 1
                continue
            
            text = markdown_to_text(body)

            converted = {
                'id': 'reddit:' + id_,
                'text': text,
                'meta': {
                    'sourcemeta': data,
                }
            }
            print(json.dumps(converted, ensure_ascii=False))

    if dup_count > 0 or deleted_count > 0:
        logging.warning(f'skipped {deleted_count} deleted entries and '
                        f'{dup_count} entries with duplicate IDs')


def main(argv):
    args = argparser().parse_args(argv[1:])

    for fn in args.jsonl:
        convert_reddit(fn, args)


if __name__ == '__main__':
    sys.exit(main(sys.argv))
