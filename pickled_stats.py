import sys

from collections import Counter
from argparse import ArgumentParser
import json
from pickled import PickledDataset


def argparser():
    ap = ArgumentParser()
    ap.add_argument('pickle', nargs='+')
    ap.add_argument('--save_as_json',
                    default=False,
                    action='store_true')
    ap.add_argument('--out_json_name',
                    default="out.json")
    ap.add_argument('--recalculate',
                   action='store_true',
                   default=False)
    return ap

def print_from_json(filepath):
    with open(filepath) as f:
        json_file = json.loads(f.read())
        print("TOTAL:", json_file['total_count'])

def main(argv):
    args = argparser().parse_args(argv[1:])
    from os.path import exists
    if not exists(f'{args.pickle[0]}.json') or args.recalculate:
        counts = {}
        total_count = 0
        print(args.pickle[0])
        for fn in args.pickle:
            stats = Counter()
            for i, example in enumerate(PickledDataset(fn)):
                for k, v in example.items():
                    print(i, end="\r", file=sys.stderr)
                    stats[f'{k}[{len(v)}]'] += 1
                stats['TOTAL'] += 1
            for k, v in reversed(sorted(stats.items())):
                print(f'{fn}: {v} {k}')

            counts[fn] = {
                "num_rows" : stats['TOTAL'],
                "dims":  [key for key in stats.keys()][:-1],
            }
            total_count += stats['TOTAL']

        if args.save_as_json:
                
            if len(args.pickle)==1: 
            #and args.pickle[0].split("/")[-1] in ['train.pickle','dev.pickle']:
                outname = args.pickle[0]+'.json'
            else:
                outname = args.out_json_name
            with open(outname,'wt') as outfile:
                json.dump({
                    "counts": counts,
                    "total_count": total_count
                }, outfile,indent=2)
    else:
        print("Calculated file already present.")
        print_from_json(f'{args.pickle[0]}.json')

if __name__ == '__main__':
    sys.exit(main(sys.argv))

