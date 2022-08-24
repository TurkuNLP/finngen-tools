#!/bin/bash
#SBATCH --cpus-per-task=10
#SBATCH --mem=100G
#SBATCH -p pilot
#SBATCH -t 00:10:00
#SBATCH --gpus-per-node=mi250:8
#SBATCH --ntasks-per-node=1
#SBATCH --nodes=10
##SBATCH --exclude=nid005162,nid005151,nid005165,nid005156,nid005154,nid005164,nid005150,nid005158,nid005159,nid005161,nid005179,nid005157,nid005167,nid005163,nid005160,nid005166,nid005170,nid005197
#SBATCH --account=project_462000119
#SBATCH -o logs/gpt-%j.out
#SBATCH -e logs/gpt-%j.err

rm -f logs/latest.out logs/latest.err
ln -s gpt-$SLURM_JOBID.out logs/latest.out
ln -s gpt-$SLURM_JOBID.err logs/latest.err

#module load CrayEnv
module load cray-python 
export NCCL_SOCKET_IFNAME=hsn0,hsn1,hsn2,hsn3

echo "START $SLURM_JOBID: $(date)"

srun -l ./pretrain_gpt.sh $1

echo "END $SLURM_JOBID: $(date)"
