import os
import pickle

import datasets

from dataclasses import dataclass
from typing import Optional
import json
from torch.utils.data import IterableDataset
from datasets import IterableDatasetDict
from datasets.splits import Split, SplitDict, SplitGenerator


logger = datasets.utils.logging.get_logger(__name__)


class PickledDatasetIterator:
    def __init__(self, filepath):
        self.file = open(filepath, 'rb')
        self.keys = None
        self._load_batch()

    def _load_batch(self):
        try:
            self.batch = pickle.load(self.file)
        except EOFError:
            raise StopIteration

        keys = sorted(list(self.batch.keys()))
        if self.keys is None:
            self.keys = keys    # first batch
        elif keys != self.keys:
            raise ValueError('keys differ between batches')

        self.batch_size = len(self.batch[keys[0]])
        assert all(len(self.batch[k]) == self.batch_size for k in self.keys)
        self.batch_offset = 0

    def __next__(self):
        if self.batch_offset >= self.batch_size:
            self._load_batch()
        d = { 
            k: self.batch[k][self.batch_offset].tolist()
            for k in self.keys 
        }
        # TODO add parameter controlling addition of labels
        if 'labels' not in d:
            d['labels'] = d['input_ids']
        self.batch_offset += 1
        return d


class PickledDataset(IterableDataset):
    def __init__(self, filepath):
        super().__init__()
        self.filepath = filepath
        self._column_names = None
        try:
            with open(self.filepath+'.json') as f:
                stats = json.loads(f.read())
                print(stats)
                self.size = stats['total_count']
        except:
            self.size = 0
        

    def __len__(self):
        return self.size
               
    def __iter__(self):
        return PickledDatasetIterator(self.filepath)
    
#    def __len__(self):
#        return self.dataset_size

#    def set_len(self, dataset_size):
#        print("dataset length set to ",dataset_size)
#        self.dataset_size = dataset_size

    @property
    def column_names(self):
        if self._column_names is None:
            example = next(iter(self))
            self._column_names = list(example.keys())
        return self._column_names


class PickledDatasetBuilder(datasets.DatasetBuilder):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        print(kwargs)
        self.data_dir = kwargs['data_dir']
        self.split_paths = {}
        
    def _info(self):
        return datasets.DatasetInfo(
            description='pickled dataset'
        )

    def download_and_prepare(self, dl_manager=None, **kwargs):
        # Mostly no-op: data assumed to be on disk and not cached.
        if dl_manager is not None:
            logger.warning('ignoring dl_manager')

        split_generators = self._split_generators(self.data_dir)
        split_dict = SplitDict(dataset_name=self.name)
        for split_generator in split_generators:
            split_dict.add(split_generator.split_info)
            self._prepare_split(split_generator, **kwargs)
        self.info.splits = split_dict

    def as_dataset(self, split: Optional[Split]=None, **kwargs):
        # By default, return all splits
        if split is None:
            splits = self.info.splits
        else:
            splits = [split]
        datasets = {
            s: self._as_dataset(s) for s in splits
        }
        return IterableDatasetDict(datasets)

    def _as_dataset(self, split: Split):
        filepath = self.split_paths[split]
        return PickledDataset(filepath)

    def _split_generators(self, data_dir):
        return [
            datasets.SplitGenerator(
                name=datasets.Split.TRAIN,
                gen_kwargs={
                    "filepath": os.path.join(data_dir, "train.pickle"),
                    "split": "train",
                }
            ),
            datasets.SplitGenerator(
                name=datasets.Split.VALIDATION,
                gen_kwargs={
                    "filepath": os.path.join(data_dir, "dev.pickle"),
                    "split": "dev",
                }
            ),
            datasets.SplitGenerator(
                name=datasets.Split.TEST,
                gen_kwargs={
                    "filepath": os.path.join(data_dir, "test.pickle"),
                    "split": "test"
                }
            )
        ]

    def _prepare_split(self, split_generator: SplitGenerator, **kwargs):
        # Mostly no-op: data assumed to be on disk and preprocessed.
        # Simply store the mapping from split name to path.
        filepath = split_generator.gen_kwargs['filepath']
        self.split_paths[split_generator.name] = filepath
