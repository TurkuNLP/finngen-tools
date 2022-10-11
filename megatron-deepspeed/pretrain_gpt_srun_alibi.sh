set -xe
export wd=$(pwd)
export subdir=kb-runs-gpt_alibi

mkdir -p $wd/$subdir  
cd $wd/$subdir
rm -rf $wd/$subdir/run-*.log $wd/$subdir/checkpoints #NOTE: remove previous logs and checkpoints

CHECKPOINT_PATH=checkpoints/gpt-base
DATA_PATH=$wd/../openwebtext2/merged
VOCAB_FILE=$wd/gpt2-tokenizer/vocab.json
MERGE_FILE=$wd/gpt2-tokenizer/merges.txt

module load cray-python
source $wd/../venv/bin/activate

### SLURM RESOURCES

export NNODES=2
export NPROC_PER_NODE=8

export MICRO_BATCH_SIZE=15
export GRAD_ACC_STEPS=1
export TP=4
export PP=2
export ZERO_STAGE=1
export GLOBAL_BATCH_SIZE=$((MICRO_BATCH_SIZE*NPROC_PER_NODE*GRAD_ACC_STEPS*NNODES))
export EXIT_INTERVAL=100000
config_json="$wd/ds_configs/ds_config.$SLURM_JOBID.json"

#Deepspeed figures out GAS dynamically from dynamic GBS via set_train_batch_size()
cat <<EOT > $config_json
{
  "train_batch_size": $GLOBAL_BATCH_SIZE,
  "gradient_clipping": 1.0,

  "zero_optimization": {
    "stage": $ZERO_STAGE
  },
  "fp16": {
    "enabled": true,
    "loss_scale": 0,
    "loss_scale_window": 1000,
    "hysteresis": 2,
    "min_loss_scale": 1,
    "initial_scale_power": 32
  },

  "steps_per_print": 2000,
  "wall_clock_breakdown": false,
  
  "flops_profiler": {
    "enabled": true,
    "profile_step": 10,
    "module_depth": -1,
    "top_modules": 1,
    "detailed": true
    }
}
EOT


  cat > helper.sh << EOF
#!/bin/bash -ex

mpids=''
if [ \$SLURM_LOCALID -eq 0 ] ; then
  ../rocm-monitor.sh &
  mpids=\$!
fi


export OUTPUT_DIR=$subdir/ds_megatron_output
export TENSORBOARD_PATH=$OUTPUT_DIR/tensorboard
export FLOPS_PATH=$OUTPUT_DIR/flops

export NCCL_SOCKET_IFNAME=hsn0,hsn1,hsn2,hsn3
export MASTER_ADDR=\$(scontrol show hostname "\$SLURM_NODELIST" | head -n1)
echo \$MASTER_ADDR

export MASTER_PORT=34567
export OMP_NUM_THREADS=2
export WORLD_SIZE=\$SLURM_NTASKS
export RANK=\$SLURM_PROCID
export LOCAL_RANK=\$SLURM_LOCALID
unset ROCR_VISIBLE_DEVICES


#          --rampup-batch-size 2 2 1_000 \


GPT_ARGS="--num-layers 24 \
          --hidden-size 1024 \
          --tensor-model-parallel-size $TP \
          --pipeline-model-parallel-size $PP \
          --num-attention-heads 16 \
          --seq-length 2048 \
          --max-position-embeddings 2048 \
          --ffn-hidden-size 4096 \
          --micro-batch-size $MICRO_BATCH_SIZE \
          --global-batch-size $GLOBAL_BATCH_SIZE \
          --optimizer adam \
          --adam-beta1 0.9 \
          --adam-beta2 0.95 \
          --adam-eps 1e-8 \
          --lr 3e-4 \
          --min-lr 1e-5 \
          --train-iters 10000 \
          --lr-warmup-iters 200 \
          --lr-decay-style cosine \
          --lr-decay-iters 100000 \
          --clip-grad 1.0 \
          --weight-decay 1e-1 \
          --embed-layernorm \
          --fp16 \
          --partition-activations \
          --seed 42 \
          --position-embedding-type alibi \
          --data-path $DATA_PATH \
          --vocab-file $VOCAB_FILE \
          --merge-file $MERGE_FILE \
          --split 949,50,1 \
          --local_rank \$LOCAL_RANK"

OUTPUT_ARGS="--log-interval 100 \
            --save-interval 5000 \
            --eval-interval 1000 \
            --eval-iters 100 \
            --tensorboard-dir $subdir/tensorboard \
            --tensorboard-queue-size 5 \
            --log-timers-to-tensorboard \
            --log-batch-size-to-tensorboard \
            --log-validation-ppl-to-tensorboard \
            "

# DEEPSPEED_ARGS="--deepspeed --deepspeed_config $config_json  " 
DEEPSPEED_ARGS=" \
    --deepspeed \
    --deepspeed_config ${config_json} \
    --zero-stage ${ZERO_STAGE} \
    --deepspeed-activation-checkpointing \
    "

cmd="python3 \
       $wd/pretrain_gpt.py \
       \$GPT_ARGS \
       \$OUTPUT_ARGS \
       --save $CHECKPOINT_PATH \
       --load $CHECKPOINT_PATH \
       \$DEEPSPEED_ARGS"
\$cmd --exit-interval $EXIT_INTERVAL |& tee run-\$SLURM_PROCID.log

for p in \$mpids ; do
  kill \$p
done

EOF
  chmod +x helper.sh 
  MASKS="ff000000000000,ff00000000000000,ff0000,ff000000,ff,ff00,ff00000000,ff0000000000"
  srun --mem 80G --account project_462000119 -ppilot --time=02:00:00 -N $NNODES -n $((NNODES*NPROC_PER_NODE)) \
  --gpus=$(($NPROC_PER_NODE*$NNODES)) \
  --cpus-per-task=8 --cpu-bind=mask_cpu:$MASKS \
  ./helper.sh |& tee run-complete.log

#   srun --jobid=$MYSLURMID -N $NNODES -n $((NNODES*NPROC_PER_NODE)) \
#   --gpus=$((8*$NNODES)) \
#   --cpus-per-task=8 --cpu-bind=mask_cpu:$MASKS \
#   ./helper.sh |& tee run-complete.log