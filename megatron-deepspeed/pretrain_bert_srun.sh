  set -xe
  export wd=/scratch/project_462000069/risto/Megatron-DeepSpeed
  mkdir -p $wd/kb-runs
  cd $wd/kb-runs
  rm -rf $wd/kb-runs/run-*.log $wd/kb-runs/checkpoints #NOTE: remove previous logs and checkpoints

  CHECKPOINT_PATH=checkpoints/bert_tiny
  DATA_PATH=$wd/bert-data_2_text_sentence
  VOCAB_FILE=$wd/bert-base-cased-tokenizer/vocab.txt

  module load cray-python
  source $wd/../venv/bin/activate

### SLURM RESOURCES
  export NNODES=2
  export NPROC_PER_NODE=8


  export MICRO_BATCH_SIZE=64
  export GRAD_ACC_STEPS=1
  export ZERO_STAGE=1

config_json="$wd/ds_configs/ds_config.$SLURM_JOBID.json"

#Deepspeed figures out GAS dynamically from dynamic GBS via set_train_batch_size()
cat <<EOT > $config_json
{
  "gradient_accumulation_steps": $GRAD_ACC_STEPS,
  "train_micro_batch_size_per_gpu": $MICRO_BATCH_SIZE,
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
  #rocm-monitor &
  mpids=\$!
fi


export OUTPUT_DIR=kb-runs/ds_megatron_output
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




BERT_ARGS="--num-layers 12 \
           --hidden-size 768 \
           --num-attention-heads 12 \
           --seq-length 512 \
           --no-pipeline-parallel \
           --max-position-embeddings 512 \
           --lr 7e-4 \
           --train-iters 100000 \
           --lr-warmup-iters 1000 \
           --micro-batch-size $MICRO_BATCH_SIZE \
           --global-batch-size $((MICRO_BATCH_SIZE*1*NPROC_PER_NODE*NNODES)) \
           --adam-beta2 0.999 \
           --adam-eps 1e-6 \
           --data-path $DATA_PATH \
           --vocab-file $VOCAB_FILE \
           --split 949,50,1 \
           --fp16 \
           --tokenizer-type BertWordPieceCase --local_rank \$LOCAL_RANK"

OUTPUT_ARGS="--log-interval 10 \
             --save-interval 5000 \
             --eval-interval 1000 \
             --eval-iters 10"
DEEPSPEED_ARGS="--deepspeed --deepspeed_config $config_json"
cmd="python3 \
       $wd/pretrain_bert.py \
       \$BERT_ARGS \
       \$OUTPUT_ARGS \
       --save $CHECKPOINT_PATH \
       --load $CHECKPOINT_PATH \
       \$DEEPSPEED_ARGS"

\$cmd --exit-interval 100 |& tee run-\$SLURM_PROCID.log

for p in \$mpids ; do
  kill \$p
done

EOF
  chmod +x helper.sh 
  MASKS="ff000000000000,ff00000000000000,ff0000,ff000000,ff,ff00,ff00000000,ff0000000000"
  srun --account project_462000119 -ppilot --time=01:00:00 -N $NNODES -n $((NNODES*NPROC_PER_NODE)) \
  --gpus=$((8*$NNODES)) \
  --cpus-per-task=8 --cpu-bind=mask_cpu:$MASKS \
  ./helper.sh |& tee run-complete.log
#   srun --jobid=$MYSLURMID -N $NNODES -n $((NNODES*NPROC_PER_NODE)) \
#   --gpus=$((8*$NNODES)) \
#   --cpus-per-task=8 --cpu-bind=mask_cpu:$MASKS \
#   ./helper.sh |& tee run-complete.log