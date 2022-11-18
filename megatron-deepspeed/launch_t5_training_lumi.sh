#!/bin/bash
#SBATCH --cpus-per-task=10
#SBATCH --mem=100G
#SBATCH --partition pilot 
#SBATCH -t 10:00:00
#SBATCH --gpus-per-node=mi250:4
#SBATCH --ntasks-per-node=1
#SBATCH --nodes=1
#SBATCH --account=project_462000119
#SBATCH --job-name=setup-testg4
#SBATCH -o logs/t5-%j.out
#SBATCH -e logs/t5-%j.err

mkdir -p logs

rm -f logs/latest.out logs/latest.err
ln -s t5-$SLURM_JOBID.out logs/latest.out
ln -s t5-$SLURM_JOBID.err logs/latest.err

export ROCBLAS_INTERNAL_FP16_ALT_IMPL=1 
export MIOPEN_DEBUG_CONVOLUTION_ATTRIB_FP16_ALT_IMPL=1
export NCCL_SOCKET_IFNAME=hsn0,hsn1,hsn2,hsn3

module load cray-python 

echo "START $SLURM_JOBID: $(date)"

srun -l ./pretrain_t5_lumi.sh 

echo "END $SLURM_JOBID: $(date)"
