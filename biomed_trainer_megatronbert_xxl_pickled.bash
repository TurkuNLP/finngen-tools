#!/bin/bash
#SBATCH --job-name=biomegatronbert-pickle
#SBATCH --account=project_2004600
#SBATCH --time=36:00:00
#SBATCH --partition=gpumedium
#SBATCH --nodes=2
#SBATCH --mem=120G
#SBATCH --cpus-per-task=64
#SBATCH --gres=gpu:a100:4
#SBATCH -o logs/%j.out
#SBATCH -e logs/%j.err

#
rm -f logs/latest.out logs/latest.err
ln -s $SLURM_JOBID.out logs/latest.out
ln -s $SLURM_JOBID.err logs/latest.err
#

DATA_DIR=/scratch/project_2004600/biomedical-data/week_14/biomed-pickled-data/biomed-100p-pickled-nonfiltered-dataset/
MODEL_OUTPUTDIR=/scratch/project_2004600/risto/011221-biomegatron-bert-xxlarge-100p-test-4/
CONFIG_OVERRIDES="num_hidden_layers=36,hidden_size=1296,num_attention_heads=24,intermediate_size=4860"

NUM_EPOCHS=2
PER_GPU_BATCH_SIZE=12
BASE_LEARNING_RATE=2e-05
GRADIENT_ACCUMULATION_STEPS=5

GPUS=$(echo $SLURM_JOB_GPUS | tr -s ', ' '[\n*]' | wc -l)
echo "$GPUS gpu per node count"
GPUS_PER_NODE=4
module load pdsh/2.31

export TORCH_EXTENSIONS_DIR=/scratch/project_2004600/risto/torch_ext_dir/

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

echo "$NODELIST" | perl -pe 's/$/ slots='"$GPUS"'/' > "$HOSTFILE"

MASTER_NODE=$(scontrol show hostnames "$SLURM_JOB_NODELIST" | head -n 1)
cat $HOSTFILE
NCCL_DEBUG=INFO

export TMPDIR=/scratch/project_2004600/risto
export HF_DATASETS_CACHE=$TMPDIR/"dataset_cache/"
echo "Using TEMP-dir " $HF_DATASETS_CACHE
export SING_IMAGE=/scratch/project_2004600/containers/ds-torch-131021.sif
export SING_FLAGS="$SING_FLAGS -B /appl/spack/v014/install-tree/gcc-4.8.5/pdsh-2.31-cdzt5w/bin/:/usr/local/sbin,$(pwd)/node_init.sh:/data/ --nv"
echo $SING_FLAGS
#export NCCL_DEBUG=INFO

# `scontrol show hostnames` turns condenced nodelist
# (e.g. "g[1102,1201]") into list of host names (e.g. "g1102\ng1102")
NODELIST=$(scontrol show hostnames "$SLURM_JOB_NODELIST")

#NUM_NODES=$(echo "$NODELIST" | wc -l)
#MASTER_NODE=$(echo "$NODELIST" | head -n 1)
#echo "MASTER_NODE $MASTER_NODE, NUM_NODES $NUM_NODES"

# Create deepspeed hostfile.
#HOSTFILE=hostfiles/$SLURM_JOBID.txt
#rm -f hostfiles/latest.txt
#ln -s $SLURM_JOBID.txt hostfiles/latest.txt
#echo "$NODELIST" | perl -pe 's/$/ slots='"$GPUS_PER_NODE"'/' > "$HOSTFILE"


#TRAIN_EXAMPLES=$(
#    python3 ../../../finngen-tools/pickled_stats.py "$DATA_DIR/train.pickle" 2>/dev/null | cut -d' ' -f 2
#echo "done." >&2
TRAIN_EXAMPLES=34088094
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


echo "start running trainer script"
# 
#	--train_file /scratch/project_2004600/biomedical-data/tests/data.txt \
#    --train_file /scratch/project_2004600/biomedical-data/tests/data.txt \
#singularity_wrapper exec python run_mlm.py 

DS_CONFIG=ds_config.json
singularity_wrapper exec ds_report 
singularity_wrapper exec deepspeed --hostfile=$HOSTFILE --master_addr=$MASTER_NODE run_mlm_pickled.py  \
    --model_type megatron-bert \
	--tokenizer_name biobert-tokenizer-10p/ \
	--per_device_train_batch_size $PER_GPU_BATCH_SIZE \
	--per_device_eval_batch_size $PER_GPU_BATCH_SIZE \
	--config_overrides $CONFIG_OVERRIDES \
	--overwrite_output_dir \
	--cache_dir $HF_DATASETS_CACHE \
	--resume_from_checkpoint /scratch/project_2004600/risto/011221-biomegatron-bert-xxlarge-100p-test-3/checkpoint-20000/ \
    --do_train \
	--do_eval \
	--learning_rate $LEARNING_RATE \
	--dataset_name "pickled" \
	--data_dir $DATA_DIR \
	--preprocessed \
	--gradient_accumulation_steps $GRADIENT_ACCUMULATION_STEPS \
	--eval_accumulation_steps $GRADIENT_ACCUMULATION_STEPS \
	--logging_strategy "steps" \
	--max_steps $MAX_STEPS \
	--logging_steps 200 \
	--evaluation_strategy "steps" \
	--eval_steps 5000 \
	--save_strategy "steps"\
	--save_steps 2000 \
	--max_seq_length 512 \
	--preprocessing_num_workers $SLURM_CPUS_PER_TASK \
    --output_dir $MODEL_OUTPUTDIR \
	--deepspeed $DS_CONFIG \
	--fp16

echo "END $SLURM_JOBID: $(date)"

seff $SLURM_JOB_ID >> $MODEL_OUTPUTDIR"seff.txt"
cp logs/$SLURM_JOB_ID.out $MODEL_OUTPUTDIR"log.out"
cp logs/$SLURM_JOB_ID.err $MODEL_OUTPUTDIR"log.err"
cp $DS_CONFIG $MODEL_OUTPUTDIR
