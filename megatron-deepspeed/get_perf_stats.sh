#!/bin/bash

for p in "$@"; do
    for s in "samples per second" "TFLOPs"; do
	a=$(egrep " $s: " "$p" | perl -pe 's/.*? '"$s"': (\S+).*/$1/' | sort -n | tr '\n' ',' | perl -pe 's/,$//')
    d=$(egrep -o "world size: [0-9]*" $p | cut -d " " -f 3) 
	if [ -z "$a" ]; then
	    echo "$p: $s: no values found"
	else
	    o=$(python3 -c 'from statistics import mean, stdev; a=['"$a"']; print(f"mean {mean(a):.1f}, stdev {stdev(a):.1f} ({len(a)} values {min(a):.1f}-{max(a):.1f})")')
	    echo "$p: GPUS: $d, $s: $o"
	fi
    done
done