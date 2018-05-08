#!/usr/bin/env python3
"""Fork LSST repos into a showow GitHub organization."""

import argparse
import textwrap
import os
from time import sleep
import progressbar
from .. import codetools


def parse_args():
    """Parse command-line arguments"""
    parser = argparse.ArgumentParser(
        prog='github-fork-repos',
        description=textwrap.dedent("""
        Fork LSST into a shadow GitHub organization.
        """),
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog='Part of codekit: https://github.com/lsst-sqre/sqre-codekit')
    parser.add_argument(
        '-u', '--user',
        required=True,
        help='GitHub username')
    parser.add_argument(
        '-o', '--org',
        dest='shadow_org',
        required=True,
        help='Organization to fork repos into')
    parser.add_argument(
        '--token-path',
        default='~/.sq_github_token',
        help='Use a token (made with github-auth) in a non-standard location')
    parser.add_argument(
        '-d', '--debug',
        action='store_true',
        default=os.getenv('DM_SQUARE_DEBUG'),
        help='Debug mode')
    parser.add_argument('-v', '--version', action=codetools.ScmVersionAction)
    return parser.parse_args()


def main():
    """Fork all repos into shadow org"""
    args = parse_args()

    if args.debug:
        print('You are', args.user)

    ghb = codetools.login_github(token_path=args.token_path)

    # get the organization object
    organization = ghb.organization('lsst')

    # list of all LSST repos
    repos = [g for g in organization.repositories()]
    repo_count = len(repos)

    if args.debug:
        print(repos)

    widgets = ['Forking: ', progressbar.Bar(), ' ', progressbar.AdaptiveETA()]
    pbar = progressbar.ProgressBar(
        widgets=widgets, max_value=repo_count).start()
    repo_idx = 0
    for repo in repos:
        if args.debug:
            print(repo.name)

        repo.create_fork(args.shadow_org)  # NOQA
        sleep(2)
        pbar.update(repo_idx)
        repo_idx += 1


if __name__ == '__main__':
    main()
