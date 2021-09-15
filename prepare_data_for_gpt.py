#!/usr/bin/env python3

import sys
import os
import json
import tracemalloc

from pathlib import Path
from functools import wraps
from time import time
from random import shuffle
from struct import pack
from datetime import datetime
from argparse import ArgumentParser

from tqdm import tqdm
from transformers import AutoTokenizer


def argparser():
    ap = ArgumentParser(description='Prepare data for GPT-like model training')
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


@monitored
def load_texts(paths):
    log(f'loading {len(paths)} file(s)')
    texts = []
    for path in tqdm(paths):
        with open(path) as f:
            texts.append(f.read())
    return texts


@monitored
def tokenize_and_vectorize_texts(texts, tokenizer):
    log(f'tokenizing and vectorizing {len(texts)} text(s)')
    vectors = []
    for text in tqdm(texts):
        vectors.append(tokenizer(text).input_ids)
    return vectors


@monitored
def prepare_examples(vectors, block_size):
    log(f'preparing examples from {len(vectors)} vector(s)')
    concatenated = sum(vectors, [])
    length = len(concatenated)
    # Note: this drops the remainder
    length = (length // block_size) * block_size
    chunked = [
        concatenated[i:i+block_size]
        for i in tqdm(range(0, length, block_size))
    ]
    return chunked


@monitored
def save_examples(examples, path):
    Path(os.path.dirname(path)).mkdir(parents=True, exist_ok=True)
    dim = len(examples[0])    # assume all equal size

    log(f'saving {len(examples)} examples to {path}')
    with open(path, 'wb') as f:
        for e in examples:
            f.write(pack(f'<{dim}H', *e))

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
    tokenizer = AutoTokenizer.from_pretrained(args.tokenizer)

    log('start processing')
    texts = load_texts(paths)

    vectors = tokenize_and_vectorize_texts(texts, tokenizer)
    texts = None    # discard

    examples = prepare_examples(vectors, args.block_size)
    vectors = None    # discard

    shuffle(examples)    # random order

    save_examples(examples, args.output)
    log('processing complete')


if __name__ == '__main__':
    sys.exit(main(sys.argv))
