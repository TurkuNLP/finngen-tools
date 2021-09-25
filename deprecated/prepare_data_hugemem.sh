#!/bin/bash

#SBATCH --partition=hugemem
#SBATCH --mem=1428G
#SBATCH --time=24:00:00
#SBATCH --cpus-per-task=40
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

# assume script is run on a drive with space
CACHEDIR="$PWD/datasets_cache_$SLURM_JOBID"

export HF_DATASETS_CACHE="$CACHEDIR"

# wipe cache on exit
function on_exit {
    rm -f "$CACHEDIR"
}
trap on_exit EXIT

NUM_WORKERS=$SLURM_CPUS_PER_TASK

echo "START $SLURM_JOBID: $(date)"

python prepare_data.py \
       --data "$DATADIR" \
       --tokenizer "$TOKENIZER" \
       --output_dir "$OUTDIR" \
       --num_workers $NUM_WORKERS \
       --in_memory_max_size 1024

#       --disable_cache

seff $SLURM_JOBID

echo "END $SLURM_JOBID: $(date)"
