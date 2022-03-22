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
    ap.add_argument(
        '--mean_noise_span_length',
        default=3.0,
        help='Mean span length of masked tokens. Value will be stored in output-file metadata'
    )
    ap.add_argument(
        '--mlm_probability',
        default=0.15,
        help='Ratio of tokens to mask for span masged language modeling loss'
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
        with open(path, encoding="utf8", errors='ignore') as f: # omit invalid characters such as zero width space (U+200b)
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


def compute_input_and_target_lengths(inputs_length, noise_density, mean_noise_span_length):
    """This function is copy of `random_spans_helper <https://github.com/google-research/text-to-text-transfer-transformer/blob/84f8bcc14b5f2c03de51bd3587609ba8f6bbd1cd/t5/data/preprocessors.py#L2466>`__ .
    Training parameters to avoid padding with random_spans_noise_mask.
    When training a model with random_spans_noise_mask, we would like to set the other
    training hyperparmeters in a way that avoids padding.
    This function helps us compute these hyperparameters.
    We assume that each noise span in the input is replaced by extra_tokens_per_span_inputs sentinel tokens,
    and each non-noise span in the targets is replaced by extra_tokens_per_span_targets sentinel tokens.
    This function tells us the required number of tokens in the raw example (for split_tokens())
    as well as the length of the encoded targets. Note that this function assumes
    the inputs and targets will have EOS appended and includes that in the reported length.
    Args:
        inputs_length: an integer - desired length of the tokenized inputs sequence
        noise_density: a float
        mean_noise_span_length: a float
    Returns:
        tokens_length: length of original text in tokens
        targets_length: an integer - length in tokens of encoded targets sequence
    """

    def _tokens_length_to_inputs_length_targets_length(tokens_length):
        num_noise_tokens = int(round(tokens_length * noise_density))
        num_nonnoise_tokens = tokens_length - num_noise_tokens
        num_noise_spans = int(round(num_noise_tokens / mean_noise_span_length))
        # inputs contain all nonnoise tokens, sentinels for all noise spans
        # and one EOS token.
        _input_length = num_nonnoise_tokens + num_noise_spans + 1
        _output_length = num_noise_tokens + num_noise_spans + 1
        return _input_length, _output_length

    tokens_length = inputs_length

    while _tokens_length_to_inputs_length_targets_length(tokens_length + 1)[0] <= inputs_length:
        tokens_length += 1

    inputs_length, targets_length = _tokens_length_to_inputs_length_targets_length(tokens_length)

    # minor hack to get the targets length to be equal to inputs length
    # which is more likely to have been set to a nice round number.
    if noise_density == 0.5 and targets_length > inputs_length:
        tokens_length -= 1
        targets_length -= 1
    return tokens_length, targets_length



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
def prepare_examples(paths, tokenizer, args, expanded_input_length):
    texts = load_texts(paths, args.max_lines)
    vectors = tokenize_and_vectorize_texts(texts, tokenizer,truncation = args.line_by_line)
    examples = create_blocks(vectors, expanded_input_length) if not args.line_by_line else vectors
    return list(examples)


@monitored
def save_examples(examples, args, expanded_input_length):
    path = args.output
    Path(os.path.dirname(path)).mkdir(parents=True, exist_ok=True)
    dim = len(examples[0])    # assume all equal size

    log(f'saving {len(examples)} examples to {path}')
    with open(path, 'wb') as f:
        for batch in batch_examples(examples, args.batch_size):
            pickle.dump(batch, f)

    log(f'saving metadata to {path}.json')
    with open(f'{path}.json', 'wt') as f:
        json.dump({
            'dim': dim,
            'num_rows': len(examples),
            'expanded_input_length': expanded_input_length,
            'mlm_probability': args.mlm_probability,
            'mean_noise_span_length': args.mean_noise_span_length,
            'max_seq_length': args.block_size,
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



    expanded_inputs_length, targets_length = compute_input_and_target_lengths(
        inputs_length=args.block_size,
        noise_density=args.mlm_probability,
        mean_noise_span_length=args.mean_noise_span_length,
    )

    log(f'loading tokenizer "{args.tokenizer}"')
    tokenizer = AutoTokenizer.from_pretrained(args.tokenizer)
    if args.line_by_line:
        tokenizer.model_max_length=args.block_size


    log('start processing')
    examples = prepare_examples(paths, tokenizer, args, expanded_inputs_length)

    log('shuffling examples')
    shuffle(examples)    # random order

    log('saving')
    save_examples(examples, args, expanded_inputs_length)
    log('done.')


if __name__ == '__main__':
    sys.exit(main(sys.argv))
