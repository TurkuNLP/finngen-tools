#!/usr/bin/env python3

# Extract text from WET files and convert inta a simple JSONL format
# with keys 'id', 'text', and 'meta'.

import sys
import json
import gzip
import functools
import logging

from collections import defaultdict
from argparse import ArgumentParser

from warcio.archiveiterator import ArchiveIterator


def argparser():
    ap = ArgumentParser()
    ap.add_argument('-v', '--verbose', default=False, action='store_true')
    ap.add_argument('wet', nargs='+')
    return ap


def get_record_id(record):
    return record.rec_headers.get_header('WARC-Record-ID')


def get_refers_to(record):
    return record.rec_headers.get_header('WARC-Refers-To')


def get_target_uri(record):
    return record.rec_headers.get_header('WARC-Target-URI')


def get_record_date(record):
    return record.rec_headers.get_header('WARC-Date')


def get_content_length(record):
    return int(record.rec_headers.get_header('Content-Length'))


def get_mime_type(record):
    type_ = record.rec_headers.get_header('WARC-Identified-Payload-Type')
    if type_ is not None:
        return type_
    else:
        return record.rec_headers.get_header('Content-Type')


def clean_id(id_):
    assert id_.startswith('<') and id_.endswith('>')
    return id_[1:-1]


def process_stream(flo):
    logging.info(f'START processing {flo.name}')
    for record in ArchiveIterator(flo):
        if record.rec_type != 'conversion':
            continue
        id_ = clean_id(get_refers_to(record))
        wet_id = clean_id(get_record_id(record))
        uri = get_target_uri(record)
        type_ = get_mime_type(record)
        date = get_record_date(record)
        length = get_content_length(record)
        content = record.content_stream().read().decode('utf-8')

        data = {
            'id': f'commoncrawl:{id_}',
            'text': content,
            'meta': {
                'wet_id': wet_id,
                'uri': uri,
                'source_type': type_,
                'download_date': date,
                'source_length': length,
            },
        }
        print(json.dumps(data, ensure_ascii=False))


def main(argv):
    args = argparser().parse_args(argv[1:])

    logging.basicConfig()
    if args.verbose:
        logging.getLogger().setLevel(logging.INFO)

    for fn in args.wet:
        if fn.endswith('.gz'):
            with gzip.open(fn) as f:
                process_stream(f)
        else:
            with open(fn, 'rb') as f:
                process_stream(f)


if __name__ == '__main__':
    sys.exit(main(sys.argv))
