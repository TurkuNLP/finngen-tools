#!/bin/bash
module load cray-python 
source ../venv/bin/activate
echo "Number of gpus-on node $SLURMD_NODENAME: $SLURM_GPUS_PER_NODE"

echo "checkin ip a"
ip a
# Distributed args
export OMP_NUM_THREADS=$SLURM_CPUS_PER_TASK
ZERO_STAGE=1
GPUS_PER_NODE=$(echo $SLURM_GPUS_PER_NODE | cut -d ":" -f 2)
NNODES=$SLURM_NNODES
N_GPUS=$((GPUS_PER_NODE*NNODES))
MASTER_ADDR=$(scontrol show hostnames $SLURM_JOB_NODELIST | head -n 1)
MASTER_PORT=6000
WORLD_SIZE=$((GPUS_PER_NODE*NNODES))
GRAD_ACC_STEPS=1
BATCH_SIZE_PER_GPU=60
NODE_RANK=$SLURM_PROCID
GLOBAL_BATCH_SIZE=$((WORLD_SIZE*BATCH_SIZE_PER_GPU))
TORCH_DISTRIBUTED_DEBUG=INFO

OUTPUT_DIR=/scratch/project_462000069/risto/ds_megatron_output
TENSORBOARD_PATH=$OUTPUT_DIR/tensorboard
FLOPS_PATH=$OUTPUT_DIR/flops
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


CHECKPOINT_PATH=/scratch/project_2004600/risto/megatron-bert/checkpoints/bert-large
#Remove previous checkpoints, needed if amount nodes != amount nodes
# rm -rf $CHECKPOINT_PATH
VOCAB_FILE=bert-base-cased-tokenizer/vocab.txt
DATA_PATH=bert-data_2_text_sentence  #Does not give rights to other group members by default
BERT_ARGS="--num-layers 24 \
          --hidden-size 1024 \
          --no-pipeline-parallel \
          --num-attention-heads 16 \
          --seq-length 512 \
          --split 949,50,1 \
          --max-position-embeddings 512\
          --distributed-backend nccl \
          --micro-batch-size $BATCH_SIZE_PER_GPU \
          --global-batch-size $GLOBAL_BATCH_SIZE \
          --lr 0.0001 \
          --train-iters 200 \
          --lr-decay-iters 99 \
          --vocab-file $VOCAB_FILE \
          --data-impl mmap \
          --clip-grad 1.0 \
          --lr-warmup-fraction .01 \
          --fp16 \
          "


    # pretrain_bert.py \
    # --tensor-model-parallel-size $TENSOR_PARALLEL \
    # --pipeline-model-parallel-size $PIPELINE_PARALLEL \
    # --num-layers $NUM_LAYERS \
    # --hidden-size $HIDDEN_SIZE \
    # --num-attention-heads $NUM_ATTENTION_HEADS \
    # --seq-length $SEQ_LENGTH \
    # --max-position-embeddings $MAX_POSITION_EMBEDDINGS \
    # --micro-batch-size $MICRO_BATCH_SIZE \
    # --global-batch-size $GLOBAL_BATCH_SIZE \
    # --lr 0.00015 \
    # --train-iters 500000 \
    # --lr-decay-iters 320000 \
    # --lr-decay-style cosine \
    # --vocab-file $VOCAB_FILE \
    # --lr-warmup-fraction 0.01 \
    # --fp16 \
    # --split 949,50,1 \
    # --log-interval 10 \
    # --save-interval 500 \
    # --eval-interval 100 \
    # --eval-iters 10 \
    # --save $CHECKPOINT_PATH \
    # --load $CHECKPOINT_PATH \
    # --data-path $DATA_PATH \
    # --deepspeed \
    # --deepspeed_config ds_config.json



OUTPUT_ARGS="--log-interval 10 \
             --save-interval 500 \
             --eval-interval 100 \
             --eval-iters 10 \
             --tensorboard-dir $TENSORBOARD_PATH \
             "


# DEEPSPEED_ARGS=" \
#     --deepspeed \
#     --deepspeed_config ${config_json} \
#     --zero-stage ${ZERO_STAGE} \
#     "
export TORCH_LAUNCHER="python -u -m torch.distributed.launch \
    --nproc_per_node $GPUS_PER_NODE \
    --nnodes $NNODES \
    --master_addr $MASTER_ADDR \
     --master_port $MASTER_PORT 
    "
# export TORCH_LAUNCHER="python3 -m torch.distributed.run \
#     --nnodes=$SLURM_JOB_NUM_NODES \
#     --nproc_per_node=$GPUS_PER_NODE \
#     --rdzv_id=$SLURM_JOB_ID \
#     --rdzv_backend=c10d \
#     --rdzv_endpoint="$RDZV_HOST:$RDZV_PORT"
#     "


if [[ $1 = "--no-deepspeed" ]]; then
    DEEPSPEED_ARGS=""
else
    DEEPSPEED_ARGS="--deepspeed --deepspeed_config $config_json"
fi

RUN_PYTHON_COMMAND="pretrain_bert.py \
        $BERT_ARGS \
        $OUTPUT_ARGS \
        --save $CHECKPOINT_PATH \
        --load $CHECKPOINT_PATH \
        --data-path $DATA_PATH $DEEPSPEED_ARGS"

echo "Launching BERT-like training with the following parameters:"      
echo "$TORCH_LAUNCHER --node rank $SLURM_PROCID $RUN_PYTHON_COMMAND"

MONITOR_PID=""
if [ $SLURM_LOCALID -eq 0 ]; then
    ./rocm-monitor.sh &
    MONITOR_PID=$!
fi


$TORCH_LAUNCHER --node_rank $SLURM_PROCID $RUN_PYTHON_COMMAND


if [ ! -z $MONITOR_PID ]; then
    kill $MONITOR_PID
fi