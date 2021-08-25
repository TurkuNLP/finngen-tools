import sys

from pathlib import Path
from functools import wraps
from time import time
from argparse import ArgumentParser

from datasets import load_dataset
from transformers import AutoTokenizer


def argparser():
    ap = ArgumentParser(description='Prepare data for GPT-like model training')
    ap.add_argument(
        '--data',
        required=True,
        help='path to data'
    )
    ap.add_argument(
        '--output_dir',
        required=True,
        help='directory to save prepared dataset in'
    )
    ap.add_argument(
        '--tokenizer',
        required=True,
        help='tokenizer name or path'
    )
    ap.add_argument(
        '--num_workers',
        type=int,
        default=10,
        help='number of workers'
    )
    ap.add_argument(
        '--block_size',
        type=int,
        default=512,
        help='example size in tokens'
    )
    return ap


def timed(f, out=sys.stderr):
    @wraps(f)
    def wrapper(*args, **kwargs):
        start = time()
        result = f(*args, **kwargs)
        print('{} completed in {:.1f} sec'.format(f.__name__, time()-start),
              file=out)
        return result
    return wrapper


@timed
def load_text(paths):
    dataset = load_dataset(
        'text',
        data_files=paths
    )
    return dataset


@timed
def tokenize_text(data, tokenizer, args):
    return data.map(
        lambda d: tokenizer(d['text']),
        batched=True,
        num_proc=args.num_workers,
        remove_columns=data['train'].column_names,
        desc='running tokenizer'
    )


@timed
def prepare_examples(data, args):
    # Following https://github.com/huggingface/transformers/blob/master/examples/pytorch/language-modeling/run_clm.py#L401
    def prepare(examples):
        concatenated = { k: sum(examples[k], []) for k in examples.keys() }
        length = len(concatenated[list(examples.keys())[0]])
        # Note: this drops the remainder
        length = (length // args.block_size) * args.block_size
        chunked = {
            k: [t[i : i + args.block_size] for i in range(0, length, args.block_size)]
            for k, t in concatenated.items()
        }
        chunked['labels'] = chunked['input_ids'].copy()
        return chunked

    return data.map(
        prepare,
        batched=True,
        batch_size=1000,
        num_proc=args.num_workers,
        desc='preparing examples'
    )

    
def main(argv):
    args = argparser().parse_args(argv[1:])
    
    paths = [str(x) for x in Path(args.data).glob("**/*.txt")]
    data = load_text(paths)

    tokenizer = AutoTokenizer.from_pretrained(args.tokenizer)
    data = tokenize_text(data, tokenizer, args)
    
    data = prepare_examples(data, args)

    data.save_to_disk(args.output_dir)


if __name__ == '__main__':
    sys.exit(main(sys.argv))
