#!/usr/bin/env python3

import sys
import os
import json
import pickle
import tracemalloc

import numpy as np

from pathlib import Path
from functools import wraps
from time import time
from random import shuffle
from datetime import datetime
from argparse import ArgumentParser

from tqdm import tqdm
from transformers import AutoTokenizer,BertTokenizerFast


def argparser():
    ap = ArgumentParser(description='Prepare data for BERT-like model training')
    ap.add_argument(
        '--input',
        required=True,
        help='path to input text file or directory'
    )
    ap.add_argument(
        '--output',
        required=True,
        help='path to save prepared data to'
    )
    ap.add_argument(
        '--tokenizer',
        default='tokenizer',
        help='tokenizer name or path'
    )
    ap.add_argument(
        '--block_size',
        type=int,
        default=1024,
        help='example size in tokens'
    )
    ap.add_argument(
        '--batch_size',
        type=int,
        default=100,
        help='number of examples per batch'
    )
    ap.add_argument(
        '--line_by_line',
        default=False,
        action='store_true',
        help='truncate each line in text to block size'
    )
    ap.add_argument(
        '--max_lines',
        type=int,
        default=1024,
        help='max number of lines to process at once'
    )
    ap.add_argument(
        '--overwrite',
        default=False,
        action='store_true',
        help='allow output to overwrite existing file'
    )
    return ap


def bytefmt(i):
    affix = iter(['B', 'KB', 'MB', 'GB', 'TB', 'PB', 'EB'])
    while i > 1024:
        i /= 1024
        next(affix)
    return f'{i:.1f}{next(affix)}'


def monitored(f, out=sys.stderr):
    @wraps(f)
    def wrapper(*args, **kwargs):
        tracemalloc.start()
        start = time()
        result = f(*args, **kwargs)
        mem, peak = tracemalloc.get_traced_memory()
        print(f'{f.__name__} completed in {time()-start:.1f} sec, '
              f'using {bytefmt(mem)}, peak {bytefmt(peak)}',
              file=out, flush=True)
        tracemalloc.stop()
        return result
    return wrapper


def now():
    return datetime.now().replace(microsecond=0).isoformat()


def log(message):
    print(f'{now()}: {message}', file=sys.stderr, flush=True)


def load_texts(paths, max_lines=1000):
    log(f'loading {len(paths)} file(s)')
    total = 0
    lines = []
    for path in paths:
        with open(path) as f:
            for ln, line in enumerate(f, start=1):
                
                lines.append(line)
                if len(lines) >= max_lines:
                    yield ''.join(lines)
                    lines = []
            if lines:
                yield ''.join(lines)
            log(f'loaded {ln} lines(s) from {path}')
            total += ln
    log(f'loaded {total} line(s) from {len(paths)} file(s)')


def tokenize_and_vectorize_texts(texts, tokenizer,truncation=False):
    for text in texts:
        yield tokenizer(text,truncation=truncation).input_ids


def create_blocks(vectors, block_size):
    concatenated = []
    for vector in vectors:
        concatenated += vector
        while len(concatenated) >= block_size:
            block, rest = concatenated[:block_size], concatenated[block_size:]
            concatenated = rest
            yield np.array(block, dtype='int32')
    # Note: this drops the remainder


def batch_examples(examples, batch_size=100):
    for i in range(0, len(examples), batch_size):
        yield {
            'input_ids': np.stack(examples[i:i+batch_size]).astype('<H')
        }


@monitored
def prepare_examples(paths, tokenizer, args):
    texts = load_texts(paths, args.max_lines)
    vectors = tokenize_and_vectorize_texts(texts, tokenizer,truncation = args.line_by_line)
    examples = create_blocks(vectors, args.block_size) if not args.line_by_line else vectors
    return list(examples)


@monitored
def save_examples(examples, path, batch_size):
    Path(os.path.dirname(path)).mkdir(parents=True, exist_ok=True)
    dim = len(examples[0])    # assume all equal size

    log(f'saving {len(examples)} examples to {path}')
    with open(path, 'wb') as f:
        for batch in batch_examples(examples, batch_size):
            pickle.dump(batch, f)

    log(f'saving metadata to {path}.json')
    with open(f'{path}.json', 'wt') as f:
        json.dump({
            'dim': dim,
            'num_rows': len(examples)
        }, f)


def main(argv):
    args = argparser().parse_args(argv[1:])

    if os.path.exists(args.output) and not args.overwrite:
        print(f'{args.output} exists, call with --overwrite to overwrite',
              file=sys.stderr)
        return 1

    if os.path.isfile(args.input):
        # single file
        paths = [args.input]
    else:
        # assume directory
        paths = [str(p) for p in Path(args.input).glob("**/*.txt")]

    if not paths:
        print(f'{args.input}: No such file or no .txt files in directory')
        return 1

    log(f'loading tokenizer "{args.tokenizer}"')
    tokenizer = BertTokenizerFast.from_pretrained(args.tokenizer)
    if args.line_by_line:
        tokenizer.model_max_length=args.block_size

    log('start processing')
    examples = prepare_examples(paths, tokenizer, args)

    log('shuffling examples')
    shuffle(examples)    # random order

    log('saving')
    save_examples(examples, args.output, args.batch_size)
    log('done.')


if __name__ == '__main__':
    sys.exit(main(sys.argv))
