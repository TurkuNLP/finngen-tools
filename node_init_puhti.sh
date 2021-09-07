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
module load gcc/9.1.0 cuda/11.1.0 pytorch/1.9
