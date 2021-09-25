import sys
import os
import json
 
import datasets

from pathlib import Path
from functools import wraps
from time import time
from struct import pack
from argparse import ArgumentParser

from datasets import Dataset, DatasetDict
from datasets import load_dataset, set_caching_enabled
from transformers import AutoTokenizer
from tqdm import tqdm


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
        '--in_memory_max_size',
        type=int,
        default=None,
        help='max size of dataset to keep in memory (in GB)'
    )
    ap.add_argument(
        '--disable_cache',
        default=False,
        action='store_true',
        help='perform processing in memory (no disk cache)'
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
        default=1024,
        help='example size in tokens'
    )
    ap.add_argument(
        '--binary',
        default=False,
        action='store_true',
        help='save in minimal binary format'
    )
    return ap


def timed(f, out=sys.stderr):
    @wraps(f)
    def wrapper(*args, **kwargs):
        start = time()
        result = f(*args, **kwargs)
        print(f'{f.__name__} completed in {time()-start:.1f} sec',
              file=out, flush=True)
        return result
    return wrapper


@timed
def load_text(paths, args):
    if not args.disable_cache:
        return load_dataset(
            'text',
            data_files=paths
        )
    else:
        # set_caching_enabled(False) or keep_in_memory=True don't
        # appear to eliminate the intial cached version of the data
        # that load_dataset creates, so use from_dict instead
        texts = []
        for p in tqdm(paths):
            with open(p) as f:
                texts.extend([s for s in f.read().splitlines() if s])
        print(f'read {len(texts)} lines from {len(paths)} files.')
        dataset = Dataset.from_dict({
            'text': texts
        })
        datasets = DatasetDict()
        datasets['train'] = dataset
        return datasets


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
            k: [
                t[i : i + args.block_size] 
                for i in range(0, length, args.block_size)
            ]
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


@timed
def save_binary(datasets, output_dir):
    Path(output_dir).mkdir(parents=True, exist_ok=True)
    
    for name, dataset in datasets.items():
        cols = dataset.column_names
        dim = len(dataset[cols[0]][0])
        assert all(len(dataset[c][0]) == dim for c in cols)

        with open(os.path.join(output_dir, f'{name}.json'), 'wt') as f:
            json.dump({
                'num_rows': dataset.num_rows,
                'column_names': cols,
                'dim': dim
            }, f)

        with open(os.path.join(output_dir, f'{name}.vec'), 'wb') as f:
            for d in dataset:
                for c in cols:
                    f.write(pack(f'<{dim}H', *d[c]))

    
def main(argv):
    args = argparser().parse_args(argv[1:])

    if args.in_memory_max_size:
        max_bytes = 1024**3 * args.in_memory_max_size
        datasets.config.IN_MEMORY_MAX_SIZE = max_bytes

    if args.disable_cache:
        set_caching_enabled(False)

    if os.path.isfile(args.data):
        paths = [args.data]
    else:
        # assume directory
        paths = [str(p) for p in Path(args.data).glob("**/*.txt")]
    data = load_text(paths, args)

    tokenizer = AutoTokenizer.from_pretrained(args.tokenizer)
    data = tokenize_text(data, tokenizer, args)
    
    data = prepare_examples(data, args)

    if not args.binary:
        data.save_to_disk(args.output_dir)
    else:
        save_binary(data, args.output_dir)


if __name__ == '__main__':
    sys.exit(main(sys.argv))
