# finngen-tools

Data preprocessing tools for Finnish corpuses. Dataset specific directories are prefixed in a style of `<NAME>-tools` and include necessary information for downloading corpuses and some supplementary statistics. 

The following scipts are used for specific preprocessing steps:

## Heuristic filtering

https://github.com/TurkuNLP/finngen-tools/blob/main/filter_jsonl.py

## Deduplication:

https://github.com/spyysalo/onion-tools

http://corpus.tools/wiki/Onion

## N-gram model filtering
https://github.com/TurkuNLP/finngen-tools/blob/main/kenlm_line_filter.py

## Toxicity filtering
https://github.com/TurkuNLP/toxicity-classifier

## Masking personal data
https://github.com/TurkuNLP/finngen-tools/tree/main/preproc-tools