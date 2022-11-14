#!/bin/bash
#SBATCH --cpus-per-task=10
#SBATCH --mem=100G
#SBATCH --partition pilot
#SBATCH -t 00:10:00
#SBATCH --gpus-per-node=mi250:8
#SBATCH --ntasks-per-node=1
#SBATCH --nodes=1
#SBATCH --account=project_462000119
#SBATCH --job-name=setup-test
#SBATCH -o logs/bert-%j.out
#SBATCH -e logs/bert-%j.err

rm -f logs/latest.out logs/latest.err
ln -s bert-$SLURM_JOBID.out logs/latest.out
ln -s bert-$SLURM_JOBID.err logs/latest.err

export NCCL_SOCKET_IFNAME=hsn0,hsn1,hsn2,hsn3

module load cray-python 
# export RDZV_HOST=$(hostname)
# export RDZV_PORT=9999               


echo "START $SLURM_JOBID: $(date)"

srun -l ./pretrain_bert.sh $1
# srun -l examples/pretrain_bert_distributed.sh

echo "END $SLURM_JOBID: $(date)"