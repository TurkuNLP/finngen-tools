#!/usr/bin/env python3

import sys
import os

from argparse import ArgumentParser

from tokenizers import Tokenizer
from tokenizers.models import Unigram
from tokenizers.normalizers import NFKC
from tokenizers.pre_tokenizers import ByteLevel
from tokenizers.decoders import ByteLevel as ByteLevelDecoder
from tokenizers.trainers import UnigramTrainer
from transformers import PreTrainedTokenizerFast


def argparser():
    ap = ArgumentParser()
    ap.add_argument(
        'files',
        nargs='+',
        help='Files with input texts'
    )
    ap.add_argument(
        '--output_dir',
        default='unigram_tokenizer',
        help='Directory to save tokenizer in'
    )
    ap.add_argument(
        '--vocab_size',
        type=int,
        default=50257,
        help='Vocabulary size'
    )
    ap.add_argument(
        '--overwrite',
        default=False,
        action='store_true',
        help='allow output to overwrite existing directory'
    )
    return ap


def main(argv):
    args = argparser().parse_args(argv[1:])

    if os.path.exists(args.output_dir) and not args.overwrite:
        print(f'{args.output_dir} exists, call with --overwrite to overwrite',
              file=sys.stderr)
        return 1

    tokenizer = Tokenizer(Unigram())
    tokenizer.normalizer = NFKC()
    tokenizer.pre_tokenizer = ByteLevel(add_prefix_space=True)
    tokenizer.decoder = ByteLevelDecoder(add_prefix_space=True)

    trainer = UnigramTrainer(
        vocab_size=args.vocab_size,
        special_tokens=['<|endoftext|>'],
#        unk_token=UNK,
    )

    tokenizer.train(args.files, trainer=trainer)

    fast_tokenizer = PreTrainedTokenizerFast(tokenizer_object=tokenizer)
    fast_tokenizer.save_pretrained(args.output_dir)


if __name__ == '__main__':
    sys.exit(main(sys.argv))
