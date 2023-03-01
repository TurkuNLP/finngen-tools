#!/usr/bin/env python3

import sys
import json

import torch

from random import randint
from argparse import ArgumentParser

from transformers import AutoTokenizer, AutoModelForCausalLM, set_seed
from flask import Flask, request


app = Flask(__name__)


def argparser():
    ap = ArgumentParser()
    ap.add_argument('model')
    ap.add_argument('port')
    ap.add_argument('--verbose', action='store_true')
    return ap


@app.route('/', methods=['GET', 'POST'])
def generate():
    if request.is_json:
        values = request.get_json()
    else:
        values = request.values

    prompt = values.get('prompt')
    temperature = values.get('temperature')
    min_new_tokens = values.get('min_new_tokens')
    max_new_tokens = values.get('max_new_tokens')
    no_repeat_ngram_size = values.get('no_repeat_ngram_size')
    seed = values.get('seed')

    try:
        temperature = float(temperature)
    except:
        temperature = 0.7

    try:
        min_new_tokens = int(min_new_tokens)
    except:
        min_new_tokens = None

    try:
        max_new_tokens = int(max_new_tokens)
    except:
        max_new_tokens = None

    try:
        no_repeat_ngram_size = int(no_repeat_ngram_size)
    except:
        no_repeat_ngram_size = 0

    try:
        seed = int(seed)
    except:
        seed = randint(0, 2**32)

    set_seed(seed)

    input_ = app.tokenizer(prompt, return_tensors='pt')
    input_tokens = input_.input_ids.shape[1]

    if torch.cuda.is_available():
        input_ = input_.to('cuda')

    output = app.model.generate(
        **input_,
        do_sample=True,
        temperature=temperature,
        min_length = input_tokens+min_new_tokens,
        #min_new_tokens=min_new_tokens,
        max_new_tokens=max_new_tokens,
        no_repeat_ngram_size=no_repeat_ngram_size,
    )
    generation = app.tokenizer.decode(output[0], skip_special_tokens=True)

    response = {
        'prompt': prompt,
        'temperature': temperature,
        'min_new_tokens': min_new_tokens,
        'max_new_tokens': max_new_tokens,
        'no_repeat_ngram_size': no_repeat_ngram_size,
        'generation': generation,
        'model_name': app.cli_args.model,
        'seed': seed,
    }

    if app.cli_args.verbose:
        print(
            json.dumps(response, indent=2, ensure_ascii=False),
            file=sys.stderr
        )

    return response


def main(argv):
    args = argparser().parse_args(argv[1:])
    app.cli_args = args

    app.tokenizer = AutoTokenizer.from_pretrained(args.model)
    app.model = AutoModelForCausalLM.from_pretrained(args.model)

    if torch.cuda.is_available():
        app.model.to('cuda')

    app.run(port=args.port)


if __name__ == '__main__':
    sys.exit(main(sys.argv))
