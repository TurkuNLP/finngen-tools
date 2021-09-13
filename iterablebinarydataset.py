import sys
import os
import json
import struct
import logging

from pathlib import Path

from torch.utils.data import IterableDataset


class IterableBinaryDataset(IterableDataset):
    def __init__(self, vecfn):
        jsonfn = f'{os.path.splitext(vecfn)[0]}.json'
        try:
            with open(f'{jsonfn}') as f:
                data = json.load(f)
            self.num_rows = data['num_rows']
            self.column_names = data['column_names']
            self.dim = data['dim'] 
        except:
            raise ValueError(f'error reading {jsonfn}')
        self.vecf = open(vecfn, 'rb')
        self.index = 0

    def __len__(self):
        return self.num_rows

    def __iter__(self):
        return self

    def __next__(self):
        if self.index == self.num_rows:
            # completed a pass, confirm and cycle to beginning
            if len(self.vecf.read(1)) != 0:
                raise ValueError(f'extra data in {self.vecf.name}')
            self.vecf.seek(0)
            self.index = 0
        fmt = f'<{self.dim}H'
        size = struct.calcsize(fmt)
        example = {}
        for n in self.column_names:
            data = self.vecf.read(size)
            if len(data) != size:
                raise EOFError    # unexpected EOF
            vec = struct.unpack(fmt, data)
            example[n] = vec
        self.index += 1
        return example


def load_binary_dataset(directory):
    paths = [str(p) for p in Path(directory).glob("*.vec")]
    datasets = {}
    for p in paths:
        name = os.path.splitext(os.path.basename(p))[0]
        datasets[name] = IterableBinaryDataset(p)
    return datasets


def main(argv):
    datasets = load_binary_dataset(argv[1])
    for n, d in datasets.items():
        for e in d:
            print(e)


if __name__ == '__main__':
    sys.exit(main(sys.argv))
