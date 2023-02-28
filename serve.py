#!/usr/bin/env python3

import sys

from argparse import ArgumentParser

from transformers import AutoTokenizer, AutoModelForCausalLM
from flask import Flask, request


app = Flask(__name__)


def argparser():
    ap = ArgumentParser()
    ap.add_argument('model')
    ap.add_argument('port')    
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

    input_ = app.tokenizer(prompt, return_tensors='pt')
    output = app.model.generate(
        **input_,
        do_sample=True,
        temperature=temperature,
        min_new_tokens=min_new_tokens,
        max_new_tokens=max_new_tokens,
        no_repeat_ngram_size=no_repeat_ngram_size,
    )
    generation = app.tokenizer.decode(output[0], skip_special_tokens=True)
    
    return {
        'prompt': prompt,
        'temperature': temperature,
        'min_new_tokens': min_new_tokens,
        'max_new_tokens': max_new_tokens,
        'no_repeat_ngram_size': no_repeat_ngram_size,
        'generation': generation,
    }


def main(argv):
    args = argparser().parse_args(argv[1:])

    app.tokenizer = AutoTokenizer.from_pretrained(args.model)
    app.model = AutoModelForCausalLM.from_pretrained(args.model)

    app.run(port=args.port)


if __name__ == '__main__':
    sys.exit(main(sys.argv))
