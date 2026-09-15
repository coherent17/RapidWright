#!/usr/bin/env python3
import argparse
import os
import re
import sys

IMPORT_RE = re.compile(r'^import\s+(static\s+)?([A-Za-z0-9_\.]+)(\.\*)?;\s*$')


def is_jdk_import(fqn):
    return fqn.startswith('java.') or fqn.startswith('javax.')


def sort_imports(path):
    with open(path, 'r') as f:
        lines = f.readlines()

    import_idx_map = {}
    for i, line in enumerate(lines):
        m = IMPORT_RE.match(line.strip())
        if m:
            fqn = m.group(2) + (m.group(3) or '')
            key = (not is_jdk_import(fqn), m.group(1) or '', fqn)
            import_idx_map[i] = key

    if not import_idx_map:
        return False

    first = min(import_idx_map)
    last = max(import_idx_map)

    kept = []
    for i in range(first, last + 1):
        if i not in import_idx_map:
            stripped = lines[i].strip()
            if stripped:
                kept.append(lines[i])

    sorted_idx = sorted(import_idx_map, key=lambda k: import_idx_map[k])
    jdk = [lines[i] for i in sorted_idx if not import_idx_map[i][0]]
    other = [lines[i] for i in sorted_idx if import_idx_map[i][0]]

    block = jdk
    if jdk and other:
        block.append('\n')
    block.extend(other)
    if kept:
        block.extend(kept)

    new_lines = lines[:first] + block + lines[last + 1:]
    if new_lines == lines:
        return False

    with open(path, 'w') as f:
        f.writelines(new_lines)
    return True


def main():
    parser = argparse.ArgumentParser(
        description='Reorder Java imports so JDK imports come first (CODING_STYLE.md 3.3).')
    parser.add_argument('paths', nargs='+', help='Java files or directories to process')
    parser.add_argument('--check', action='store_true',
                        help='Check only; exit 1 if any file needs import reordering')
    args = parser.parse_args()

    files = []
    for p in args.paths:
        if os.path.isdir(p):
            for root, _, fs in os.walk(p):
                for f in fs:
                    if f.endswith('.java'):
                        files.append(os.path.join(root, f))
        else:
            files.append(p)

    changed = []
    for path in sorted(set(files)):
        if sort_imports(path):
            changed.append(path)

    if args.check:
        if changed:
            print('These files have JDK imports not ordered first:')
            for p in changed:
                print('    ' + p)
            print()
            print('Run scripts/java_import_sorter.py to fix the ordering.')
            sys.exit(1)
        return

    for p in changed:
        print('Reordered imports in ' + p)
    if not changed:
        print('No import reordering needed.')


if __name__ == '__main__':
    main()