#!/usr/bin/env python3
"""Align the defsrc and deflayer blocks of kanata configs.

Every column is as wide as its longest key plus four spaces. The caps column
sits at indent 2, and the rest of the grid starts right after it. A thumb row
(e.g. spc) keeps the column it already sits under; keys after its first one
don't widen the grid, since nothing follows them.

Usage: fmt-kbd.py [--check] FILE...
  Formats each FILE in place. With --check, only reports files that would
  change, exiting with status 1 if there are any.
"""
import re
import sys

GAP = 4
CAPS_INDENT = 2
BLOCK = re.compile(r'(\((?:defsrc|deflayer \S+))\n(.*?)\n\)', re.S)


def indent(line):
    return len(line) - len(line.lstrip())


def token_starts(line):
    return [m.start() for m in re.finditer(r'\S+', line)]


def format_block(head, body):
    lines = body.strip('\n').split('\n')
    rows = [line.split() for line in lines]
    grid_indent = indent(lines[0])

    # Work out which grid column each row starts at. The caps row is indented
    # less than the grid; a thumb row is indented more, under some column.
    starts = []
    for line in lines:
        if indent(line) < grid_indent:
            starts.append(-1)
        elif indent(line) > grid_indent:
            above = max((token_starts(l) for l in lines if indent(l) == grid_indent), key=len)
            if indent(line) not in above:
                sys.exit(f'{head}: thumb row is not under any column: {line.strip()!r}')
            starts.append(above.index(indent(line)))
        else:
            starts.append(0)

    cols = {}
    for start, keys, line in zip(starts, rows, lines):
        if indent(line) > grid_indent:
            keys = keys[:1]
        for i, key in enumerate(keys):
            cols.setdefault(start + i, []).append(key)
    width = {c: max(len(k) for k in keys) + GAP for c, keys in cols.items()}

    pos = {0: CAPS_INDENT + width[-1] if -1 in width else grid_indent}
    if -1 in width:
        pos[-1] = CAPS_INDENT
    for c in range(1, max(cols) + 1):
        pos[c] = pos[c - 1] + width.get(c - 1, 1 + GAP)

    out = []
    for start, keys in zip(starts, rows):
        line = ' ' * pos[start]
        for i, key in enumerate(keys):
            last = i == len(keys) - 1
            line += key if last else key.ljust(width.get(start + i, len(key) + GAP))
        out.append(line)
    return head + '\n' + '\n'.join(out) + '\n)'


def main(args):
    check = '--check' in args
    paths = [a for a in args if a != '--check']
    if not paths:
        sys.exit(__doc__.strip())

    changed = []
    for path in paths:
        with open(path, encoding='utf-8') as f:
            old = f.read()
        new = BLOCK.sub(lambda m: format_block(m[1], m[2]), old)
        if new == old:
            continue
        changed.append(path)
        if check:
            print(f'would reformat {path}')
        else:
            with open(path, 'w', encoding='utf-8') as f:
                f.write(new)
            print(f'reformatted {path}')
    return 1 if check and changed else 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
