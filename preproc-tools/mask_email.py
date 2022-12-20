#!/usr/bin/env python3

# High recall, low precision email masking.

import sys
import regex

from argparse import ArgumentParser


AT_VAR = r'(?:@|\bat\b|\(at\)|\[at\]|\bät\b|\(ät\)|\(ät\)|\(a\)|\[a\])'
DOT_VAR = r'(?:\.|\bdot\b|\(dot\)|\[dot\]|\bpiste\b|\(piste\)|\[piste\])'

AT_VAR_RE = regex.compile(AT_VAR)
DOT_VAR_RE = regex.compile(r'('+DOT_VAR+r')')

# https://html.spec.whatwg.org/multipage/input.html#valid-e-mail-address
# extended with variations
MAYBE_EMAIL_RE = regex.compile(
    r"([a-zA-Z0-9.!#$%&'*+\/=?^_`{}~-]+)" +
    r'(\s*' + AT_VAR + r'\s*)' +
    r'((?:[a-zA-Z0-9][a-zA-Z0-9-]{0,61}[a-zA-Z0-9]\s*' + DOT_VAR + r'\s*)+'
    r'(?:[a-z]{2,8}|[A-Z]{2,8}))\b'
)

MASK_LOCAL_PART = 'email'
MASK_DOMAIN = 'example.com'


def argparser():
    ap = ArgumentParser()
    ap.add_argument('text', nargs='+')
    return ap


def domain_prefix(string, tlds):
    # Fix overmatches using list of top-level domains
    parts = DOT_VAR_RE.split(string)
    candidates = []
    for i in range(2, len(parts), 2):
        if parts[i].strip().lower() in tlds:
            candidates.append(''.join(parts[:i+1]))

    if not candidates:
        return None

    return candidates[0]    # rough heuristic


def mask_emails(string, tlds):
    if not AT_VAR_RE.search(string):
        return string    # no match possible, avoid expensive RE

    replacements = []
    for m in MAYBE_EMAIL_RE.finditer(string):
        local_part, at_symbol, domain = m.groups()
        domain = domain_prefix(m.group(3), tlds)
        if domain is None:
            continue    # not a possible email
        orig_text = local_part + at_symbol + domain
        print('HIT:', orig_text, file=sys.stderr)
        mask_text = MASK_LOCAL_PART + at_symbol + MASK_DOMAIN
        replacements.append((m.start(), m.start()+len(orig_text), mask_text))

    # replace in reversed order to preserve offsets
    for start, end, mask_text in reversed(replacements):
        before, span, after = string[:start], string[start:end], string[end:]
        string = before + mask_text + after

    return string


def load_top_level_domains(fn):
    # wget https://data.iana.org/TLD/tlds-alpha-by-domain.txt
    tlds = set()
    with open(fn) as f:
        for l in f:
            if l.startswith('#'):
                continue
            tlds.add(l.strip().lower())
    return tlds


def main(argv):
    args = argparser().parse_args(argv[1:])

    tlds = load_top_level_domains('tlds-alpha-by-domain.txt')

    for fn in args.text:
        with open(fn) as f:
            for l in f:
                print(mask_emails(l, tlds), end='')


if __name__ == '__main__':
    sys.exit(main(sys.argv))
