#!/bin/bash

# Userspace install of deepspeed on CSC mahti

#SBATCH --account=project_2004600
#SBATCH --partition=gputest
#SBATCH --time=00:15:00
#SBATCH --gres=gpu:a100:1
#SBATCH --output=logs/%j.out
#SBATCH --error=logs/%j.err

export DS_BUILD_CPU_ADAM=1
export DS_BUILD_FUSED_ADAM=1
export DS_BUILD_FUSED_LAMB=1
export DS_BUILD_SPARSE_ATTN=1
export DS_BUILD_TRANSFORMER=1
export DS_BUILD_TRANSFORMER_INFERENCE=0 # compile fails
export DS_BUILD_STOCHASTIC_TRANSFORMER=1
export DS_BUILD_UTILS=1
export DS_BUILD_AIO=0 # no libaio

rm -f logs/latest.out logs/latest.err
ln -s $SLURM_JOBID.out logs/latest.out
ln -s $SLURM_JOBID.err logs/latest.err

module purge
module load gcc/10.3.0 cuda/11.2.2 pytorch/1.9

python -m pip uninstall --yes deepspeed
python -m pip install --user deepspeed --global-option="build_ext"

# print environment report 
python -m deepspeed.env_report
