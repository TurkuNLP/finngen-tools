#!/bin/bash



module load cray-python
source ../venv/bin/activate

echo "Number of gpus-on node $SLURMD_NODENAME: $SLURM_GPUS_PER_NODE"

# Distributed args
export OMP_NUM_THREADS=$SLURM_CPUS_PER_TASK
ZERO_STAGE=1
GPUS_PER_NODE=8
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

OUTPUT_DIR=/pfs/lustrep4/scratch/project_462000119/risto/ds_megatron_output
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
    "detailed": true,
    "output_file": "($SLURM_JOBID)"
    }
}
EOT




CHECKPOINT_PATH=checkpoints/gpt2_345m
#Remove previous checkpoints, needed if amount nodes != amount nodes
rm -rf $CHECKPOINT_PATH
VOCAB_FILE=gpt2-tokenizer/vocab.json
MERGE_FILE=gpt2-tokenizer/merges.txt
DATA_PATH=../openwebtext2/merged #Does not give rights to other group members by default
GPT_ARGS="--num-layers 24 \
          --hidden-size 1024 \
          --num-attention-heads 16 \
          --seq-length 1024 \
          --max-position-embeddings 1024 \
          --micro-batch-size $BATCH_SIZE_PER_GPU \
          --global-batch-size $GLOBAL_BATCH_SIZE \
          --lr 0.00015 \
          --train-iters 100 \
          --lr-decay-iters 320000 \
          --lr-decay-style cosine \
          --vocab-file $VOCAB_FILE \
          --merge-file $MERGE_FILE \
          --data-impl mmap \
          --lr-warmup-fraction .01 \
          --fp16 \
          "


OUTPUT_ARGS="--log-interval 10 \
             --save-interval 500 \
             --eval-interval 100 \
             --eval-iters 10 \
             --checkpoint-activations \
             --tensorboard-dir $TENSORBOARD_PATH \
             "

export TORCH_LAUNCHER="python -u -m torch.distributed.launch \
    --nproc_per_node $GPUS_PER_NODE \
    --nnodes $NNODES \
    --master_addr $MASTER_ADDR \
    --master_port $MASTER_PORT \
    "
if [[ $1 = "--no-deepspeed" ]]; then
    DEEPSPEED_ARGS=""
else
    DEEPSPEED_ARGS="--deepspeed --deepspeed_config $config_json"
fi

RUN_PYTHON_COMMAND="pretrain_gpt.py \
       $GPT_ARGS \
       $OUTPUT_ARGS \
       --save $CHECKPOINT_PATH \
       --load $CHECKPOINT_PATH \
       --data-path $DATA_PATH $DEEPSPEED_ARGS"


MONITOR_PID=""
if [ $SLURM_LOCALID -eq 0 ]; then
    ./rocm-monitor.sh &
    MONITOR_PID=$!
fi


echo "Launching GPT-like training with the following parameters:"      
echo "$TORCH LAUNCHER --node rank $SLURM_PROCID $RUN_PYTHON_COMMAND"
$TORCH_LAUNCHER --node_rank $SLURM_PROCID $RUN_PYTHON_COMMAND

if [ ! -z $MONITOR_PID ]; then
    kill $MONITOR_PID
fi

