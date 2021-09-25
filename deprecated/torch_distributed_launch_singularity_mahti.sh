#!/bin/bash

# Launch script with torch.distributed.launch(). Used by SLURM
# scripts, don't invoke directly.

module purge
module load gcc/10.3.0 cuda/11.2.2 pytorch/1.9

# `scontrol show hostnames` turns condenced nodelist
# (e.g. "g[1102,1201]") into list of host names (e.g. "g1102\ng1102")
MASTER_NODE=$(scontrol show hostnames "$SLURM_JOB_NODELIST" | head -n 1)
PORT=9999

echo "Launching on $SLURMD_NODENAME ($SLURM_PROCID/$SLURM_JOB_NUM_NODES), master $MASTER_NODE port $PORT"

python -m torch.distributed.launch \
    --nnodes=$SLURM_JOB_NUM_NODES \
    --nproc_per_node=4 \
    --node_rank=$SLURM_PROCID \
    --master_addr=$MASTER_NODE \
    --master_port=$PORT \
    "$@"
