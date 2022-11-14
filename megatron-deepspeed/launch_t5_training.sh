#!/bin/bash
#SBATCH --cpus-per-task=10
#SBATCH --mem=80G
#SBATCH --partition gputest
#SBATCH -t 00:10:00
#SBATCH --gpus-per-node=v100:2
#SBATCH --ntasks-per-node=1
#SBATCH --nodes=1
#SBATCH --account=project_2004600
#SBATCH --job-name=setup-test
#SBATCH -o logs/t5-%j.out
#SBATCH -e logs/t5-%j.err

rm -f logs/latest.out logs/latest.err
ln -s t5-$SLURM_JOBID.out logs/latest.out
ln -s t5-$SLURM_JOBID.err logs/latest.err

module load pytorch 

echo "START $SLURM_JOBID: $(date)"

srun -l ./pretrain_t5.sh 

echo "END $SLURM_JOBID: $(date)"