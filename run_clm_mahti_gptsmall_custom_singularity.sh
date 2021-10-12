#!/bin/bash
#SBATCH --account=project_2004407
#SBATCH --partition=gpumedium
#SBATCH --time=36:00:00
#SBATCH --nodes=4
#SBATCH --gres=gpu:a100:4
#SBATCH --output=logs/%j.out
#SBATCH --error=logs/%j.err

DATA_DIR=data
OUTPUT_DIR=output-gptsmall
NUM_EPOCHS=10

PER_GPU_BATCH_SIZE=8
BASE_LEARNING_RATE=5e-05
GRADIENT_ACCUMULATION_STEPS=4

GPUS_PER_NODE=4

#set -euo pipefail

module purge
module load pdsh/2.31

export SING_IMAGE=/scratch/project_2004600/containers/latest.sif

#Bind directory with pdsh to /usr/local/sbin in singularity
export SING_FLAGS="$SING_FLAGS -B /appl/spack/v014/install-tree/gcc-4.8.5/pdsh-2.31-cdzt5w/bin/:/usr/local/sbin,$(pwd)/node_init.sh:/data/ --nv"


# Check that pdsh is found as expected also from singularity python
echo "Native pdsh      : $(which pdsh)"
echo "Singularity pdsh : $(singularity_wrapper exec python -c 'import shutil; print(shutil.which("pdsh"))')"

# Start from scratch
rm -rf "$OUTPUT_DIR"

# Link logs as latest.out and latest.err
rm -f logs/latest.out logs/latest.err
ln -s $SLURM_JOBID.out logs/latest.out
ln -s $SLURM_JOBID.err logs/latest.err

# `scontrol show hostnames` turns condenced nodelist
# (e.g. "g[1102,1201]") into list of host names (e.g. "g1102\ng1102")
NODELIST=$(scontrol show hostnames "$SLURM_JOB_NODELIST")

NUM_NODES=$(echo "$NODELIST" | wc -l)
MASTER_NODE=$(echo "$NODELIST" | head -n 1)
echo "MASTER_NODE $MASTER_NODE, NUM_NODES $NUM_NODES"

# Create deepspeed hostfile.
HOSTFILE=hostfiles/$SLURM_JOBID.txt
rm -f hostfiles/latest.txt
ln -s $SLURM_JOBID.txt hostfiles/latest.txt
echo "$NODELIST" | perl -pe 's/$/ slots='"$GPUS_PER_NODE"'/' > "$HOSTFILE"

echo -n "Counting number of training examples..." >&2
TRAIN_EXAMPLES=$(
    singularity_wrapper exec python pickled_stats.py "$DATA_DIR/train.pickle" 2>/dev/null |
    egrep 'TOTAL$' | perl -pe 's/.*?(\d+) TOTAL/$1/'
)
echo "done." >&2

TOTAL_TRAIN_EXAMPLES=$((TRAIN_EXAMPLES * NUM_EPOCHS))
NUM_GPUS=$((NUM_NODES*GPUS_PER_NODE))
EFFECTIVE_BATCH_SIZE=$((
	PER_GPU_BATCH_SIZE *
	NUM_GPUS *
	GRADIENT_ACCUMULATION_STEPS
))
# Add (denominator-1) to round up
MAX_STEPS=$((
	(TOTAL_TRAIN_EXAMPLES + (EFFECTIVE_BATCH_SIZE-1)) /
	EFFECTIVE_BATCH_SIZE
))
# Adjust by number of nodes
LEARNING_RATE=$(python -c 'print('"$BASE_LEARNING_RATE"'*'"$NUM_NODES"'*'"$GRADIENT_ACCUMULATION_STEPS"')')

cat <<EOF
------------------------------------------------------------------------------
TRAIN_EXAMPLES ................ $TRAIN_EXAMPLES
NUM_EPOCHS .................... $NUM_EPOCHS
PER_GPU_BATCH_SIZE ............ $PER_GPU_BATCH_SIZE
NUM_GPUS ...................... $NUM_GPUS
GRADIENT_ACCUMULATION_STEPS ... $GRADIENT_ACCUMULATION_STEPS
EFFECTIVE_BATCH_SIZE .......... $EFFECTIVE_BATCH_SIZE
MAX_STEPS ..................... $MAX_STEPS
LEARNING_RATE ................. $LEARNING_RATE
------------------------------------------------------------------------------
EOF

echo "START $SLURM_JOBID: $(date)"

singularity_wrapper exec deepspeed \
    --master_addr "$MASTER_NODE" \
    --hostfile "$HOSTFILE" \
    run_clm.py \
    --preprocessed \
    --tokenizer /projappl/project_2004600/risto/tokenizer_openai/ \
    --model_type gpt2 \
    --dataset_name "pickled" \
    --data_dir "$DATA_DIR" \
    --do_train \
    --do_eval \
    --max_steps "$MAX_STEPS" \
    --save_strategy "steps" \
    --save_steps 1000 \
    --evaluation_strategy "steps" \
    --eval_steps 1000 \
    --save_total_limit 5 \
    --per_device_train_batch_size "$PER_GPU_BATCH_SIZE" \
    --gradient_accumulation_steps "$GRADIENT_ACCUMULATION_STEPS" \
    --learning_rate "$LEARNING_RATE" \
    --output_dir "$OUTPUT_DIR" \
    --deepspeed ds_config.json

echo "END $SLURM_JOBID: $(date)"

seff $SLURM_JOBID | tee seff.txt
