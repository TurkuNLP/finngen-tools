#!/bin/bash
set -eou pipefail
module load pytorch 
echo "Number of gpus-on node $SLURMD_NODENAME: $SLURM_GPUS_PER_NODE"

MASTER_ADDR=$(scontrol show hostnames $SLURM_JOB_NODELIST | head -n 1)
MASTER_PORT=6000

GPUS_PER_NODE=$(echo $SLURM_GPUS_PER_NODE | cut -d ":" -f 2)
NNODES=$SLURM_NNODES
WORLD_SIZE=$((GPUS_PER_NODE*NNODES))
BATCH_SIZE_PER_GPU=40
GLOBAL_BATCH_SIZE=$((WORLD_SIZE*BATCH_SIZE_PER_GPU))
GRAD_ACC_STEPS=1
ZERO_STAGE=1


## GPT2BPE-tokenizer
# DATA_PATH="../openwebtext2/merged"
# VOCAB_FILE="gpt2-tokenizer/vocab.json"
# MERGE_FILE="gpt2-tokenizer/merges.txt"
# TOKENIZER_TYPE="GPT2BPETokenizer"
#TOKENIZER_ARGS="--tokenizer-type $TOKENIZER_TYPE --vocab-file $VOCAB_FILE --merge-file $MERGE_FILE"

## BertWordPieceCase
DATA_PATH="bert-data_text_sentence"
VOCAB_FILE="bert-base-cased-tokenizer/vocab.txt"
TOKENIZER_TYPE="BertWordPieceCase"
TOKENIZER_ARGS="--tokenizer-type $TOKENIZER_TYPE --vocab-file $VOCAB_FILE"



mkdir -p ds_configs

config_json="ds_configs/./ds_config.$SLURM_JOBID.json"
# Deepspeed figures out GAS dynamically from dynamic GBS via set_train_batch_size()
cat <<EOT > $config_json
{
  "gradient_accumulation_steps": $GRAD_ACC_STEPS,
  "train_micro_batch_size_per_gpu": $BATCH_SIZE_PER_GPU,
  "zero_optimization": {
    "stage": $ZERO_STAGE
  },
  "fp16": {
    "enabled": true
  },
  "steps_per_print": 2000,
  "wall_clock_breakdown": false,
  
  "flops_profiler": {
    "enabled": true,
    "profile_step": 1,
    "module_depth": -1,
    "top_modules": 1,
    "detailed": true
    }
}
EOT


CHECKPOINT_PATH=/scratch/project_2004600/risto/megatron-bert/checkpoints/t5-init
rm -rf $CHECKPOINT_PATH
DISTRIBUTED_ARGS="--nproc_per_node $GPUS_PER_NODE --nnodes $NNODES --node_rank $SLURM_PROCID --master_addr $MASTER_ADDR --master_port $MASTER_PORT"

python -m torch.distributed.launch $DISTRIBUTED_ARGS \
       pretrain_t5.py \
       --num-layers 12 \
       --hidden-size 768 \
       --num-attention-heads 12 \
       --kv-channels 64 \
       --ffn-hidden-size 3072 \
       --encoder-seq-length 512 \
       --decoder-seq-length 128 \
       --micro-batch-size $BATCH_SIZE_PER_GPU \
       --global-batch-size  $GLOBAL_BATCH_SIZE \
       --max-position-embeddings 512 \
       --train-iters 200 \
       --lr-decay-iters 99 \
       --save $CHECKPOINT_PATH \
       --load $CHECKPOINT_PATH \
       --data-path $DATA_PATH \
         $TOKENIZER_ARGS \
       --vocab-extra-ids 100 \
       --data-impl mmap \
       --split 949,50,1 \
       --lr 0.0001 \
       --min-lr 0.00001 \
       --lr-decay-style linear \
       --lr-warmup-fraction .01 \
       --weight-decay 1e-2 \
       --clip-grad 1.0 \
       --log-interval 10 \
       --save-interval 10000 \
       --eval-interval 1000 \
       --eval-iters 10 \
       --fp16 
      #  --deepspeed --deepspeed_config $config_json