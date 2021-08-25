#!/bin/bash

export HF_DATASETS_CACHE="$TMPDIR/datasets_cache"

DATADIR="texts"
OUTDIR="processed"
TOKENIZER="/projappl/project_2004600/risto/tokenizer/"
NUM_WORKERS=$SLURM_CPUS_PER_TASK

python prepare_data.py \
       --data "$DATADIR" \
       --tokenizer "$TOKENIZER" \
       --output_dir "$OUTDIR" \
       --num_workers $NUM_WORKERS
