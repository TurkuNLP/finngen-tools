#!/bin/bash

# Initialize compute node environment.

CSC_ENV_INIT='/appl/profile/zz-csc-env.sh'

if [ -f "$CSC_ENV_INIT" ]; then
    echo "$0: sourcing $CSC_ENV_INIT" >&2
    source "$CSC_ENV_INIT"
else
    echo "$0: no $CSC_ENV_INIT, exiting"
    exit 1
fi

module purge
module load gcc/10.3.0 cuda/11.2.2 pytorch/1.9
