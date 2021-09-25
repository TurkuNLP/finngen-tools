#!/bin/bash

# Run https://github.com/huggingface/transformers/blob/master/examples/tensorflow/language-modeling/run_clm.py on CSC mahti

# Use with python -m pip install --user git+https://github.com/huggingface/transformers

#SBATCH --account=project_2004600
#SBATCH --partition=gputest
#SBATCH --time=00:15:00
#SBATCH --gres=gpu:a100:1
#SBATCH --output=logs/%j.out
#SBATCH --error=logs/%j.err

OUTPUT_DIR=output_dir

# Start from scratch
rm -rf "$OUTPUT_DIR"

rm -f logs/latest.out logs/latest.err
ln -s $SLURM_JOBID.out logs/latest.out
ln -s $SLURM_JOBID.err logs/latest.err

module purge
module load gcc/10.3.0 cuda/11.2.2 pytorch/1.9

python run_clm.py \
    --tokenizer tokenizer \
    --model_type gpt2 \
    --train_file texts.txt \
    --do_train \
    --num_train_epochs 1 \
    --per_device_train_batch_size 8 \
    --output_dir "$OUTPUT_DIR"
