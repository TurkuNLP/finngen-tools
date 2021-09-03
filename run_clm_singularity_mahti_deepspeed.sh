#!/bin/bash

# Run https://github.com/huggingface/transformers/blob/master/examples/tensorflow/language-modeling/run_clm.py on CSC mahti

# Use with 
# python -m pip install --user git+https://github.com/huggingface/transformers and
# python -m pip install --user deepspeed

#SBATCH --account=project_2004600
#SBATCH --partition=gpumedium
#SBATCH --time=00:15:00
#SBATCH --nodes=2
#SBATCH --gres=gpu:a100:4
#SBATCH --output=logs/%j.out
#SBATCH --error=logs/%j.err

module purge
module load gcc/10.3.0 cuda/11.2.2 pytorch/1.9 pdsh/2.31

# Bind directory with pdsh to /usr/local/sbin in singularity
export SING_FLAGS="$SING_FLAGS -B /appl/spack/v014/install-tree/gcc-4.8.5/pdsh-2.31-cdzt5w/bin:/usr/local/sbin"

# Check that pdsh is found as expected also from singularity python
which pdsh
python -c 'import shutil; print(shutil.which("pdsh"))'

OUTPUT_DIR=output_dir

# Start from scratch
rm -rf "$OUTPUT_DIR"

rm -f logs/latest.out logs/latest.err
ln -s $SLURM_JOBID.out logs/latest.out
ln -s $SLURM_JOBID.err logs/latest.err

# `scontrol show hostnames` turns condenced nodelist
# (e.g. "g[1102,1201]") into list of host names (e.g. "g1102\ng1102")
MASTER_NODE=$(scontrol show hostnames "$SLURM_JOB_NODELIST" | head -n 1)

# Create deepspeed hostfile.
HOSTFILE=hostfiles/$SLURM_JOBID.txt
rm -f hostfiles/latest.txt
ln -s $SLURM_JOBID.txt hostfiles/latest.txt
scontrol show hostnames "$SLURM_JOB_NODELIST" \
    | perl -pe 's/$/ slots=4/' \
    > "$HOSTFILE"

./deepspeed_singularity.sh \
    --master_addr "$MASTER_NODE" \
    --hostfile "$HOSTFILE" \
    run_clm.py \
    --tokenizer tokenizer \
    --model_type gpt2 \
    --train_file texts.txt \
    --do_train \
    --num_train_epochs 1 \
    --per_device_train_batch_size 6 \
    --output_dir "$OUTPUT_DIR" \
    --deepspeed ds_config.json
