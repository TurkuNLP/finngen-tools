import random
import tracemalloc
from functools import wraps
from time import time

from datasets import load_dataset
from argparse import ArgumentParser
import sys
import pickle
import numpy as np
from pathlib import Path
import os
import json

def argparser():
    ap = ArgumentParser(description='Shuffle and save pickled data. Reads the whole dataset into a numpy.array, shuffles it and then pickles it.')
    ap.add_argument('--input_path', required=True, help="Directory containing pickled data that is read with 'pickled' using datasets.load_dataset")
    ap.add_argument('--output_path', required=True, help="Directory to save shuffled files 'dev.pickle' and 'train.pickle'")
    return ap

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

def bytefmt(i):
    affix = iter(['B', 'KB', 'MB', 'GB', 'TB', 'PB', 'EB'])
    while i > 1024:
        i /= 1024
        next(affix)
    return f'{i:.1f}{next(affix)}'

@monitored
def main(argv):
    chunk_size = 100
    args = argparser().parse_args(argv[1:])
    dataset = load_dataset('pickled', data_dir=args.input_path)
    save_path = args.output_path
    Path(os.path.dirname(save_path)).mkdir(parents=True, exist_ok=True)
    seq_len = len(next(iter(dataset['train']))['input_ids'])
    for split in ['train', 'validation'][::-1]:
        split_len = len(dataset[split])
        data = np.empty([split_len, seq_len], dtype=np.uint16)
        for i, row in enumerate(dataset[split]):
            data[i] = row['input_ids']
            print(i, end='\r')

        np.random.shuffle(data)

        # requirement for naming from from pickled/pickle.py
        if split == 'validation':
            split = 'dev'
        outname = save_path + f'{split}.pickle'

        with open(outname+'.json', 'wt') as outfile:
            json.dump({
                "counts": {
                    "dims": [seq_len],
                },
                "TOTAL": split_len,
            }, outfile, indent=2)

        with open(outname, 'wb') as f:
            for i in range(0, len(data), chunk_size):
                #print(data[i:i+chunk_size])
                pickle.dump({'input_ids': np.stack(data[i:i+chunk_size]).astype('<H')}, f)
            print(f"Created file {outname}")

if __name__ =='__main__':
    sys.exit(main(sys.argv))
