#!/bin/bash
set -eou pipefail

module load cray-python

# source /scratch/project_462000119/sampo/nov-2022-gpt-01/venv/bin/activate
echo "Number of gpus-on node $SLURMD_NODENAME: $SLURM_GPUS_PER_NODE"

MASTER_ADDR=$(scontrol show hostnames $SLURM_JOB_NODELIST | head -n 1)
MASTER_PORT=6000

GPUS_PER_NODE=$(echo $SLURM_GPUS_PER_NODE | cut -d ":" -f 2)
NNODES=$SLURM_NNODES
WORLD_SIZE=$((GPUS_PER_NODE*NNODES))
BATCH_SIZE_PER_GPU=16
GLOBAL_BATCH_SIZE=$((WORLD_SIZE*BATCH_SIZE_PER_GPU))
GRAD_ACC_STEPS=1
ZERO_STAGE=1

export ROCBLAS_INTERNAL_FP16_ALT_IMPL=1
export MIOPEN_DEBUG_CONVOLUTION_ATTRIB_FP16_ALT_IMPL=1

module use /pfs/lustrep2/projappl/project_462000125/samantao-public/mymodules
module load aws-ofi-rccl/sam-default.lua

# Uses BertWordPieceCase. 
# For just testing setup, you may use tiny-owt-example for data and vocab 
DATA_PATH=finbert-pgfv2-bert_text_document
VOCAB_FILE=vocab.txt
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


DISTRIBUTED_ARGS="--nproc_per_node $GPUS_PER_NODE --nnodes $NNODES --node_rank $SLURM_PROCID --master_addr $MASTER_ADDR --master_port $MASTER_PORT"

# Small 32EL -- 143M params (see paper)
T5_SMALL_NL32="--num-layers 32 --hidden-size 512  --num-attention-heads 8 --kv-channels 64 --ffn-hidden-size 2048"
# original config
T5_BASE="--num-layers 12 --hidden-size 768 --num-attention-heads 12  --kv-channels 64 --ffn-hidden-size 3072"
# Large 36L  -- 1.1B params (see paper)
T5_LARGE_NL36="--num-layers 36 --hidden-size 1024 --num-attention-heads 16 --kv-channels 64 --ffn-hidden-size 4096"

ARCHITECTURE=$T5_BASE

CHECKPOINT_PATH=./checkpoints/t5-$ARCHITECTURE-$SLURM_JOBID
mkdir -p $CHECKPOINT_PATH

      #  --load $CHECKPOINT_PATH \
# NOTE: orig decoder_seq_length is 128
python -m torch.distributed.launch $DISTRIBUTED_ARGS \
       pretrain_t5.py \
       $ARCHITECTURE\
       --no-pipeline-parallel \
       --encoder-seq-length 512 \
       --decoder-seq-length 128 \
       --micro-batch-size $BATCH_SIZE_PER_GPU \
       --global-batch-size  $GLOBAL_BATCH_SIZE \
       --max-position-embeddings 512 \
       --save $CHECKPOINT_PATH \
       --data-path $DATA_PATH \
         $TOKENIZER_ARGS \
       --vocab-extra-ids 100 \
       --data-impl mmap \
       --split 949,50,1 \
       --train-iters 2000000 \
       --lr-decay-iters 990000 \
       --lr 5e-04 \
       --min-lr 0.00001 \
       --lr-decay-style linear \
       --lr-warmup-fraction .001 \
       --weight-decay 1e-2 \
       --clip-grad 1.0 \
       --log-interval 100 \
       --save-interval 10000 \
       --eval-interval 5000 \
       --eval-iters 10 \
       --tensorboard-dir $CHECKPOINT_PATH/tensorboard 
       #       --deepspeed --deepspeed_config $config_json
