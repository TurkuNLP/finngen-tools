#!/usr/bin/env python3

# Based on
# https://github.com/bigscience-workshop/bs-tokenizers/blob/main/tokenizers/train_tokenizer_v3_on_subset.py

import sys
import os
import json

from argparse import ArgumentParser

from tokenizers import Tokenizer, Regex, decoders, pre_tokenizers, processors
from tokenizers.models import BPE
from tokenizers.trainers import BpeTrainer
from transformers import BloomTokenizerFast


def argparser():
    ap = ArgumentParser()
    ap.add_argument('input_jsonl')
    ap.add_argument('output_dir')
    ap.add_argument('--vocab_size', default=64000, type=int)
    ap.add_argument('--batch_size', default=1000, type=int)
    ap.add_argument('--unk_token', default='<unk>')
    ap.add_argument('--bos_token', default='<s>')
    ap.add_argument('--eos_token', default='</s>')
    ap.add_argument('--pad_token', default='<pad>')
    return ap


def load_jsonl_texts(fn):
    texts = []
    with open(fn) as f:
        for line in f:
            data = json.loads(line)
            texts.append(data['text'])
    return texts


def set_postproc_and_decoder_use_regex(tokenizer_dir):
    fn = os.path.join(tokenizer_dir, 'tokenizer.json')
    with open(fn) as f:
        data = json.load(f)

    data['post_processor']['use_regex'] = False
    data['decoder']['use_regex'] = False

    with open(fn, 'w') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


def batch_texts(texts, batch_size):
    for i in range(0, len(texts), batch_size):
        yield texts[i:i+batch_size]


def main(argv):
    args = argparser().parse_args(argv[1:])

    texts = load_jsonl_texts(args.input_jsonl)

    tokenizer = Tokenizer(BPE())
    tokenizer.pre_tokenizer = pre_tokenizers.Sequence([
        pre_tokenizers.Split(Regex(r' ?[^(\s|[.,!?…。，、।۔،])]+'), 'isolated'),
        pre_tokenizers.ByteLevel(add_prefix_space=False, use_regex=False),
    ])
    tokenizer.decoder = decoders.ByteLevel(use_regex=False)
    tokenizer.post_processor = processors.ByteLevel(trim_offsets=False)

    special_tokens = [
        args.unk_token,
        args.bos_token,
        args.eos_token,
        args.pad_token
    ]

    trainer = BpeTrainer(
        vocab_size=args.vocab_size,
        special_tokens=special_tokens,
        show_progress=True,
    )

    tokenizer.train_from_iterator(
        batch_texts(texts, args.batch_size),
        trainer=trainer,
        length=len(texts),
    )

    tokenizer_fast = BloomTokenizerFast(
        tokenizer_object=tokenizer,
        unk_token=args.unk_token,
        eos_token=args.eos_token,
        bos_token=args.bos_token,
        pad_token=args.pad_token,
        padding_side='left',
    )
    tokenizer_fast.save_pretrained(args.output_dir)

    # need this to match BLOOM tokenizer.json
    set_postproc_and_decoder_use_regex(args.output_dir)


if __name__ == '__main__':
    sys.exit(main(sys.argv))
