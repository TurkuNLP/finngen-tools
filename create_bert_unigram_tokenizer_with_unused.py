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

    tokenizer = Tokenizer(Unigram())
    tokenizer.normalizer = NFKC()
    tokenizer.pre_tokenizer = ByteLevel(add_prefix_space=True)
    tokenizer.decoder = ByteLevelDecoder(add_prefix_space=True)

    trainer = UnigramTrainer(
        vocab_size=args.vocab_size,
        special_tokens=[UNK, CLS, SEP, PAD, MASK,*UNUSED],
#        unk_token=UNK,
    )
    tokenizer.mask_token = '[MASK]'
    tokenizer.train(args.files, trainer=trainer)

    fast_tokenizer = PreTrainedTokenizerFast(tokenizer_object=tokenizer)
    fast_tokenizer.save_pretrained(args.output_dir)


if __name__ == '__main__':
    sys.exit(main(sys.argv))
