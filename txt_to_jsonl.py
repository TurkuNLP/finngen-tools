#!/usr/bin/env python

import sys
import json


def main(argv):
    for fn in argv[1:]:
        with open(fn) as f:
            for l in f:
                if l.strip():
                    print(json.dumps({ 'text': l.rstrip('\n') }))


if __name__ == '__main__':
    sys.exit(main(sys.argv))
