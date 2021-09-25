#!/bin/bash

#SBATCH --partition=medium
#SBATCH --time=24:00:00
#SBATCH --cpus-per-task=128
#SBATCH --account=project_2004600
#SBATCH --output=logs/%j.out
#SBATCH --error=logs/%j.err

DATADIR="texts"
OUTDIR="processed"
TOKENIZER="tokenizer"

rm -f logs/latest.out logs/latest.err
ln -s $SLURM_JOBID.out logs/latest.out
ln -s $SLURM_JOBID.err logs/latest.err

module purge
module load pytorch

# mahti nvme is only available on GPU nodes, so use scratch and wipe
# on exit
CACHEDIR="/scratch/$SLURM_JOB_ACCOUNT/datasets_cache_$SLURM_JOBID"

export HF_DATASETS_CACHE="$CACHEDIR"
echo "CACHE: $HF_DATASETS_CACHE"

function on_exit {
    rm -rf "$CACHEDIR"
}
trap on_exit EXIT

NUM_WORKERS=$SLURM_CPUS_PER_TASK

echo "START $SLURM_JOBID: $(date)"

python prepare_data.py \
    --data "$DATADIR" \
    --tokenizer "$TOKENIZER" \
    --output_dir "$OUTDIR" \
    --num_workers $NUM_WORKERS \
    "$@"

seff $SLURM_JOBID

echo "END $SLURM_JOBID: $(date)"
