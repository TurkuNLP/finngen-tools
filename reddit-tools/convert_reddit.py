#!/usr/bin/env python3

# Convert the JSON format in which Reddit data
# (https://files.pushshift.io/reddit/) is distributed
# into a simple JSONL format with keys 'id', 'text', and 'meta'.

import sys
import os
import re
import json
import logging

import zstandard as zstd
import inscriptis

from argparse import ArgumentParser

from markdown import markdown


def argparser():
    ap = ArgumentParser()
    ap.add_argument('--subreddit', default=None,
                    help='limit to given subreddit')
    ap.add_argument('jsonl', nargs='+')
    return ap


def normalize_paragraph_space(text):
    text = text.strip()
    lines = text.split('\n')
    lines = [re.sub(r'\s{2,}', '  ', l) for l in lines]
    lines = [l.strip() for l in lines]
    lines = [l for l in lines if l and not l.isspace()]
    text = '\n'.join(lines)
    return text


def normalize_space(text):
    text = text.strip()
    paragraphs = re.split(r'\n(?:\s*\n)+', text)
    paragraphs = [normalize_paragraph_space(p) for p in paragraphs]
    paragraphs = [p for p in paragraphs if p and not p.isspace()]
    text = '\n\n'.join(paragraphs)
    return text


def markdown_to_html(md):
    # See https://www.reddit.com/wiki/markdown/
    # TODO: consider using https://github.com/reddit/snudown

    md = md.replace('~~', '~')    # ~~strikethrough~~
    md = re.sub(r'&gt;!(.*?)!&lt;', r'\1', md)    # >!spoiler!<

    return markdown(md, extensions=['nl2br', 'tables'])


def markdown_to_text(md):
    html = markdown_to_html(md)
    text = inscriptis.get_text(html)
    text = normalize_space(text)
    return text


def convert_reddit_stream(f, fn, args):
    seen = convert_reddit_stream.seen_ids
    total_count, sr_count, dup_count, del_count, out_count = 0, 0, 0, 0, 0
    for ln, line in enumerate(f, start=1):
        total_count += 1
        try:
            data = json.loads(line)
        except Exception as e:
            logging.error(f'loading JSONL on line {ln}: {e}: "{line}"')
            continue

        if args.subreddit is not None:
            subreddit = data['subreddit']
            if subreddit != args.subreddit:
                continue
        sr_count += 1

        id_ = data.pop('id')
        if id_ in seen:
            dup_count += 1
            continue
        seen.add(id_)

        if 'title' in data:
            title = data.pop('title')
        else:
            title = None

        if 'body' in data:
            # comments have 'body'
            body = data.pop('body')
        else:
            # submissions have 'selftext'
            body = data.pop('selftext')

        if body in ('[deleted]', '[removed]'):
            del_count += 1
            continue

        text = markdown_to_text(body)

        if title:
            title = ' '.join(title.split())
            title = markdown_to_text(title)
            text = title + '\n\n' + text
            text = normalize_space(text)

        converted = {
            'id': 'reddit:' + id_,
            'text': text,
            'meta': {
                'sourcemeta': data,
            }
        }
        print(json.dumps(converted, ensure_ascii=False))
        out_count += 1

    print(f'{os.path.basename(fn)}: processed {total_count} entries,',
          (f'{sr_count} in subreddit,' if args.subreddit is not None else ''),
          f'skipped {dup_count} due to duplicate IDs,',
          f'skipped {del_count} deleted/removed,',
          f'output {out_count}.',
          file=sys.stderr)
convert_reddit_stream.seen_ids = set()


def convert_reddit(fn, args):
    if not fn.endswith('.zst'):
        with open(fn) as f:
            convert_reddit_stream(f, fn, args)
    else:
        dctx = zstd.ZstdDecompressor(max_window_size=2**31)
        with zstd.open(fn, 'rt', dctx=dctx) as f:
            convert_reddit_stream(f, fn, args)


def main(argv):
    args = argparser().parse_args(argv[1:])

    for fn in args.jsonl:
        convert_reddit(fn, args)


if __name__ == '__main__':
    sys.exit(main(sys.argv))
