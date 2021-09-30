#!/usr/bin/env python3

# Print average FLOPS from deepspeed log.

import sys
import re


FLOPS_RE = re.compile(r'^FLOPS per GPU = .*:\s*([0-9.]+) (\S+FLOPS)$')


PREFIX_MULTIPLIER = {
    'k': 1e3,
    'M': 1e6,
    'G': 1e9,
    'T': 1e12,
    'P': 1e15,
    'E': 1e18,
    'Z': 1e21,
    'Y': 1e24,
}


def to_float(value, prefix):
    try:
        multiplier = PREFIX_MULTIPLIER[prefix]
    except KeyError:
        raise ValueError(f'unknown prefix {prefix}')
    return value * multiplier


def siformat(value):
    affix = iter([''] + list(PREFIX_MULTIPLIER.keys()))
    while value > 1000:
        value /= 1000
        next(affix)
    return f'{value:.1f} {next(affix)}'


def main(argv):
    if len(argv) < 2:
        print(f'Usage: {__file__} LOGFILE [LOGFILE ...]', file=sys.stderr)
        return 1

    strings, values = [], []
    for fn in argv[1:]:
        with open(fn) as f:
            for ln, l in enumerate(f, start=1):
                m = FLOPS_RE.match(l)
                if not m:
                    continue
                value, units = m.groups()
                strings.append(f'{value} {units}')
                values.append(to_float(float(value), units[0]))

    total, count = sum(values), len(values)
    print(f'{count} values:', ' '.join(strings))
    print(f'Average: {siformat(total/count)}FLOPS')


if __name__ == '__main__':
    sys.exit(main(sys.argv))

