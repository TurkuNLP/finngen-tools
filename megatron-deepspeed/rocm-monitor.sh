#!/bin/bash

if [ -z $SLURM_JOB_ID ]; then
    echo "$0: don't invoke this directly, it is intended for use by slurm scripts. (Exiting.)"
    exit 1
fi

OUTDIR="smi-output"
OUTFILE="${SLURM_JOB_ID}-${SLURMD_NODENAME}"
OUTPATH="$OUTDIR/$OUTFILE"

mkdir -p "$OUTDIR"

touch "$OUTPATH"
ln -f -s "$OUTFILE" "$OUTDIR/latest-${SLURMD_NODENAME}"

while true; do
    rocm-smi >> "$OUTPATH" 2>&1
    sleep 1
done