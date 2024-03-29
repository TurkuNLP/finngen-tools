#!/usr/bin/env python3

# Convert https://github.com/attardi/wikiextractor output to JSONL.

import sys
import json
import re

from glob import glob
from argparse import ArgumentParser


# Document start and end lines
DOC_START_RE = re.compile(r'^<doc id="(.*?)" url="(.*?)" title="(.*?)">$')

DOC_END_RE = re.compile(r'^</doc>')


def argparser():
    ap = ArgumentParser()
    ap.add_argument('dir')
    return ap


def normalize_paragraph_space(text):
    # remove trailing whitespace, limit number of consecutive spaces,
    # and replace non-breaking with regular space
    lines = text.split('\n')
    lines = [l.rstrip() for l in lines]
    lines = [l.replace('\xa0', ' ') for l in lines]
    lines = [re.sub(r'\s{2,}', '  ', l) for l in lines]
    return '\n'.join(lines)


def normalize_space(text):
    paragraphs = re.split(r'\n(\s+\n|\n)+', text)
    paragraphs = [normalize_paragraph_space(p) for p in paragraphs]
    paragraphs = [p for p in paragraphs if p and not p.isspace()]
    return '\n\n'.join(paragraphs)


def output_document(start_line, lines, args):
    m = DOC_START_RE.match(start_line)
    id_, url, title = m.groups()
    text = '\n'.join(lines)
    text = normalize_space(text)
    data = {
        'id': f'fiwiki:{title}',
        'text': text,
        'meta': {
            'url': url,
        }
    }
    print(json.dumps(data, ensure_ascii=False))


def convert_wikiextractor(fn, args):
    count, current_start, current_lines = 0, None, None
    with open(fn) as f:
        for ln, line in enumerate(f, start=1):
            line = line.rstrip('\n')
            if DOC_START_RE.match(line):
                assert current_start is None
                current_start = line
                current_lines = []
            elif DOC_END_RE.match(line):
                assert current_start is not None
                output_document(current_start, current_lines, args)
                current_start = current_lines = None
                count += 1
            else:
                assert current_lines is not None
                current_lines.append(line)
        assert current_start is None
    return count


def main(argv):
    args = argparser().parse_args(argv[1:])

    total = 0
    for fn in sorted(glob(f'{args.dir}/**/wiki_*')):
        total += convert_wikiextractor(fn, args)

    print(f'output {total} documents.', file=sys.stderr)


if __name__ == '__main__':
    sys.exit(main(sys.argv))
