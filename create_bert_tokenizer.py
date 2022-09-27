#!/usr/bin/env python3

import sys
import os
import json

from pathlib import Path
from argparse import ArgumentParser

from tokenizers import BertWordPieceTokenizer
import time

def log(message):
    y, n, d, h, m, s = time.localtime()[:6]
    print(f"[{y}-{n}-{d} {h}:{m}:{s}] {message}")


# BERT special tokens
UNK, CLS, SEP, PAD, MASK = '[UNK]', '[CLS]', '[SEP]', '[PAD]', '[MASK]'
# Add unused token#
UNUSED = [f'[unused{i}]' for i in range(1,103)]

SPECIAL_TOKENS_MAP = {
    'unk_token': UNK,
    'sep_token': SEP,
    'pad_token': PAD,
    'cls_token': CLS,
    'mask_token': MASK,
}


def argparser():
    ap = ArgumentParser()
    ap.add_argument(
        '--files',
        help='Files with input texts'
    )
    ap.add_argument(
        '--output_dir',
        default='tokenizer',
        help='Directory to save tokenizer in'
    )
    ap.add_argument(
        '--name',
        default='bert-tokenizer',
        help='Tokenizer name'
    )
    ap.add_argument(
        '--lowercase',
        default=False,
        action='store_true',
        help='Lowercase text'
    )
    ap.add_argument(
        '--strip_accents',
        default=False,
        action='store_true',
        help='Strip accents from text'
    )
    ap.add_argument(
        '--vocab_size',
        type=int,
        default=30000,
        help='Vocabulary size'
    )
    ap.add_argument(
        '--min_frequency',
        type=int,
        default=2,
        help='Minimum token frequency'
    )
    ap.add_argument(
        '--limit_alphabet',
        type=int,
        default=1000,
        help='Maximum number of different characters in alphabet'
    )
    ap.add_argument(
        '--overwrite',
        default=False,
        action='store_true',
        help='allow output to overwrite existing directory'
    )
    return ap


def save_for_autotokenizer(tokenizer, args):
    Path(args.output_dir).mkdir(parents=True, exist_ok=True)

    tokenizer.save(os.path.join(args.output_dir, 'tokenizer.json'))
    tokenizer.save_model(args.output_dir)

    with open(os.path.join(args.output_dir, 'special_tokens_map.json'), 'w') as f:
        json.dump(SPECIAL_TOKENS_MAP, f)

    tokenizer_config = {
        'tokenizer_class': 'BertTokenizer',
        'do_lower_case': tokenizer.normalizer.lowercase,
        'strip_accents': tokenizer.normalizer.strip_accents,
        'tokenize_chinese_chars': tokenizer.normalizer.handle_chinese_chars,
        'special_tokens_map_file': 'special_tokens_map.json'
    }

    with open(os.path.join(args.output_dir, 'tokenizer_config.json'), 'w') as f:
        json.dump(tokenizer_config, f)


def main(argv):
    args = argparser().parse_args(argv[1:])

    if os.path.exists(args.output_dir) and not args.overwrite:
        print(f'{args.output_dir} exists, call with --overwrite to overwrite',
              file=sys.stderr)
        return 1

    tokenizer = BertWordPieceTokenizer(
        clean_text=True,
        handle_chinese_chars=True,
        strip_accents=args.strip_accents,
        lowercase=args.lowercase,
    )
    log('Starting to train tokenizer with config: {tokenizer}')

    tokenizer.train(
        args.files,
        vocab_size=args.vocab_size,
        min_frequency=args.min_frequency,
        show_progress=True,
        special_tokens=[UNK, CLS, SEP, PAD, MASK,*UNUSED],
        limit_alphabet=args.limit_alphabet,
    )
    log('...Done!')
    log('saving tokenizer with args: {args}')
    save_for_autotokenizer(tokenizer, args)


if __name__ == '__main__':
    sys.exit(main(sys.argv))
