#!/usr/bin/env python3

import sys

import torch

from argparse import ArgumentParser

from transformers import AutoTokenizer, AutoModelForCausalLM


def argparser():
    ap = ArgumentParser()
    ap.add_argument('--temperature', default=1.0, type=float)
    ap.add_argument('--num_beams', default=10, type=int)
    ap.add_argument('--num_return_sequences', default=3, type=int)
    ap.add_argument('model')
    ap.add_argument('file', nargs='?')
    return ap


def generate(prompts, tokenizer, model, args):
    encode = lambda s: tokenizer.encode(s, return_tensors='pt')
    decode = lambda v: tokenizer.decode(v)
    for prompt in prompts:
        prompt = prompt.rstrip('\n')

        if prompt.isspace() or not prompt:
            continue

        encoded = encode(prompt)
        if torch.cuda.is_available():
            encoded = encoded.to('cuda')

        generated = model.generate(
            encoded,
            do_sample=True,
            max_length=100,
            top_k=50,
            top_p=0.95,
            temperature=args.temperature,
            no_repeat_ngram_size=2,
            num_return_sequences=args.num_return_sequences,
            repetition_penalty=0.9,
            #bad_words_ids=[[tokenizer.eos_token_id]]
        )
        for g in generated:
            decoded = decode(g)
            decoded = decoded.replace(prompt, f'**{prompt}**', 1)
            print(decoded)
            print('-'*78)


def main(argv):
    args = argparser().parse_args(argv[1:])

    tokenizer = AutoTokenizer.from_pretrained(args.model)
    model = AutoModelForCausalLM.from_pretrained(args.model)

    if torch.cuda.is_available():
        model.to('cuda')

    print('model loaded.', file=sys.stderr)

    if not args.file:
        generate(sys.stdin, tokenizer, model, args)
    else:
        with open(args.file) as f:
            generate(f, tokenizer, model, args)


if __name__ == '__main__':
    sys.exit(main(sys.argv))
