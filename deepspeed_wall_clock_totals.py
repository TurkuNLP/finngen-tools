#!/usr/bin/env python3

# Report total wall-clock times from deepspeed log.

import sys
import re


TIMERS = [
    'forward',
    'backward_inner',
    'backward_allreduce',
    'step',
    'optimizer_gradients',
    'optimizer_step',
    'optimizer_allgather'
]

TIMER_RE = {
    t: re.compile(f' {t}: 'r'([0-9.]+)\b') for t in TIMERS
}

def main(argv):
    if len(argv) < 2:
        print(f'Usage: {__file__} LOGFILE [LOGFILE ...]', file=sys.stderr)
        return 1

    totals = { t: 0.0 for t in TIMERS }
    for fn in argv[1:]:
        with open(fn) as f:
            for ln, l in enumerate(f, start=1):
                for t, re in TIMER_RE.items():
                    m = re.search(l)
                    if m:
                        totals[t] += float(m.group(1))

    total = sum(totals.values())
    for t in TIMERS:
        print(f'{t}\t{totals[t]:.1f}\t{totals[t]/total:.1%}')


if __name__ == '__main__':
    sys.exit(main(sys.argv))
