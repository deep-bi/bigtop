#!/usr/bin/env python3

import argparse
from pathlib import Path
import re

PACKAGES_DIR = Path(__file__).parent / 'bigtop-packages/src/common'
PACKAGES = {path.name: path for path in PACKAGES_DIR.iterdir() if path.is_dir()}


def list_patches(path: Path):
    patches = path.glob('*.diff')
    digit_pattern = re.compile(r'\d+')

    def extract_number(patch):
        m = digit_pattern.search(patch.name)
        return int(m.group()) if m else 0

    patches = sorted(patches, key=extract_number)
    for patch in patches:
        print(patch.name)


def package_directory(path: Path):
    print(path.absolute())


OPERATIONS = {
    'ls': list_patches,
    'where': package_directory
}


def parse_args():
    ap = argparse.ArgumentParser()
    ap.add_argument('package', choices=PACKAGES.keys())
    ap.add_argument('operation')

    return ap.parse_args()


def main():
    args = parse_args()
    package = PACKAGES[args.package]
    operation = OPERATIONS[args.operation]

    operation(package)


if __name__ == '__main__':
    main()