#!/usr/bin/env python3

import abc
import argparse
from pathlib import Path
import re

PACKAGES_DIR = Path(__file__).parent / 'bigtop-packages/src/common'
PACKAGES = {path.name: path for path in PACKAGES_DIR.iterdir() if path.is_dir()}


class Command(abc.ABC):

    @abc.abstractmethod
    def __call__(self, args): ...

    @abc.abstractmethod
    def name(self): ...

    @abc.abstractmethod
    def configure_subparser(self, parser): ...


class ListPatches(Command):

    def __call__(self, args):
        package_directory = PACKAGES[args.package]
        patches = package_directory.glob('*.diff')
        digit_pattern = re.compile(r'\d+')

        def extract_number(patch: Path):
            m = digit_pattern.search(patch.name)
            return int(m.group()) if m else 0

        patches = sorted(patches, key=extract_number)
        for patch in patches:
            print(patch.name)

    def name(self):
        return 'ls'

    def configure_subparser(self, parser):
        pass


def list_patches(path: Path):
    patches = path.glob('*.diff')
    digit_pattern = re.compile(r'\d+')

    def extract_number(patch):
        m = digit_pattern.search(patch.name)
        return int(m.group()) if m else 0

    patches = sorted(patches, key=extract_number)
    for patch in patches:
        print(patch.name)


# def package_directory(path: Path):
    # print(path.absolute())


COMMANDS = [
    ListPatches(),
    # 'where': package_directory
]


def parse_args():
    ap = argparse.ArgumentParser()
    ap.add_argument('package', choices=PACKAGES.keys())


    subparsers = ap.add_subparsers(required=True)
    for command in COMMANDS:
        subparser = subparsers.add_parser(command.name(), parents=[ap], add_help=False)
        command.configure_subparser(subparser)
        subparser.set_defaults(func=command)

    return ap.parse_args()


def main():
    args = parse_args()
    package = PACKAGES[args.package]
    operation = COMMANDS[args.operation]

    operation(package)


if __name__ == '__main__':
    main()