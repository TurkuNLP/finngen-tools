#!/bin/bash

# Initialize compute node environment.

# When using deepspeed and pdsh, source this script in
# deepspeed/launcher/multinode_runner.py before calling
# deepspeed.launcher.launch.
CSC_ENV_INIT='/appl/profile/zz-csc-env.sh'

if [ -f "$CSC_ENV_INIT" ]; then
    echo "$0: sourcing $CSC_ENV_INIT" >&2
    source "$CSC_ENV_INIT"
else
    echo "$0: no $CSC_ENV_INIT, exiting"
    exit 1
fi

module purge
export SING_IMAGE=/scratch/project_2004600/containers/latest.sif
