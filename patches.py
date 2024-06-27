#!/usr/bin/env python3

import abc
import argparse
from pathlib import Path
import re
import subprocess

PACKAGES_DIR = Path(__file__).parent / 'bigtop-packages/src/common'
PACKAGES = {path.name: path for path in PACKAGES_DIR.iterdir() if path.is_dir()}


DIGITS_PATTERN = re.compile(r'\d+')

def extract_number(patch: Path):
    m = DIGITS_PATTERN.search(patch.name)
    return int(m.group()) if m else 0


def find_patches(package_directory: Path):
    patches = package_directory.glob('*.diff')
    return sorted(patches, key=extract_number)


class Command(abc.ABC):

    @abc.abstractmethod
    def __call__(self, args): ...

    @abc.abstractmethod
    def name(self): ...

    @abc.abstractmethod
    def help(self): ...

    @abc.abstractmethod
    def configure_subparser(self, parser): ...

class ListPatches(Command):

    def __call__(self, args):
        package_directory = PACKAGES[args.package]
        patches = find_patches(package_directory)
        for patch in patches:
            print(patch.name)

    def name(self):
        return 'ls'

    def help(self):
        return 'List patches for a package'

    def configure_subparser(self, parser):
        parser.add_argument('package', choices=PACKAGES.keys())


class ApplyPatches(Command):

    def __call__(self, args):
        package_directory = PACKAGES[args.package]
        patches = find_patches(package_directory)

        package_repo_directory = args.repository
        if not package_repo_directory.exists():
            raise ValueError(f'Repository directory {package_repo_directory} does not exist')
        
        apply_cmd = ['git', 'apply']
        apply_cmd.extend(patch.absolute() for patch in patches)

        git_add_cmd = ['git', 'add', '*']
        git_commit_cmd = ['git', 'commit', '-am', 'Applying patches']        

        if args.dry_run:
            print(f'cd {package_repo_directory}')
            print(' '.join(apply_cmd))
            print(' '.join(git_add_cmd))
            print(' '.join(git_commit_cmd))
        else:
            print(f'Applying patches to {args.package}...')
            subprocess.run(apply_cmd, cwd=package_repo_directory)
            subprocess.run(git_add_cmd, cwd=package_repo_directory)
            subprocess.run(git_commit_cmd, cwd=package_repo_directory)

    def name(self):
        return 'apply'
    
    def help(self):
        return 'Apply patches to a package. Make sure you have the repository at the BigTop requested version.'
    
    def configure_subparser(self, parser):
        parser.add_argument('package', choices=PACKAGES.keys())
        parser.add_argument('repository', type=Path, help='Path to the repository to apply patches to')
        parser.add_argument('--dry-run', action='store_true', help='Print commands instead of executing them')


class UploadRPMs(Command):

    def __init__(self, sources_dir: Path = Path('output')):
        self.sources_dir = sources_dir

    def __call__(self, args):
        base_path = Path('/mnt/repo/bigtop')
        target = args.os + ('' if args.production else 'testing')
        target_path = base_path / target

        sources = [str(rpm) for rpm in self.sources_dir.rglob('*.rpm')]
        mkdir_cmd = ['ssh', '-p', str(args.port), f'{args.user}@{args.server}', f'mkdir -p {target_path}']
        scp_cmd = ['scp', '-P', str(args.port)] + sources + [f'{args.user}@{args.server}:{target_path}']
        create_repo_cmd = ['ssh', '-p', str(args.port), f'{args.user}@{args.server}', f"'cd {target_path} ; createrepo .'"]
        if not args.dry_run:
            subprocess.run(' '.join(mkdir_cmd), text=True, shell=True)            
            if sources:
                print(f'Uploading RPMs to {args.user}@{args.server}:{target_path}...')
                subprocess.run(scp_cmd)

            # https://www.digitaldesignjournal.com/multiple-commands-with-ssh-using-python-subprocess/
            print("Updating repository metadata...")
            subprocess.run(' '.join(create_repo_cmd), shell=True, text=True)
        else:
            print('Dry run, not executing command.')
            print(' '.join(mkdir_cmd))
            if sources:
                print(' '.join(scp_cmd))
            print(' '.join(create_repo_cmd))


    def name(self):
        return 'upload-rpms'
    
    def help(self):
        return 'Upload RPMs to a repository'

    def configure_subparser(self, parser):
        if not self.sources_dir.exists():
            raise ValueError(f'Sources directory {self.sources_dir} does not exist')

        packages = (package.name for package in self.sources_dir.iterdir() if package.is_dir())

        parser.add_argument('--package', choices=list(packages), help='Package to upload RPMs for. Optional, if not provided, all packages will be uploaded.')
        parser.add_argument('--production', action='store_true', help='Upload to production repository instead of testing')
        parser.add_argument('--os', choices=['centos7', 'redhat8'], required=True, help='Operating system to upload RPMs for')
        parser.add_argument('--server', default='116.202.71.5', help='Server to upload RPMs to')
        parser.add_argument('--user', default='root', help='User to connect as')
        parser.add_argument('--port', default=22, type=int, help='Port to connect to')
        parser.add_argument('--dry-run', action='store_true', help='Print commands instead of executing them')
        


# def package_directory(path: Path):
    # print(path.absolute())


COMMANDS = [
    ListPatches(),
    UploadRPMs(),
    ApplyPatches()
    # 'where': package_directory
]


def parse_args():
    ap = argparse.ArgumentParser()

    subparsers = ap.add_subparsers(required=True)
    for command in COMMANDS:
        subparser = subparsers.add_parser(command.name(), help=command.help())
        command.configure_subparser(subparser)
        subparser.set_defaults(operation=command)

    return ap.parse_args()


def main():
    args = parse_args()
    args.operation(args)

    # operation = COMMANDS[args.operation]
    # operation(args)


if __name__ == '__main__':
    main()