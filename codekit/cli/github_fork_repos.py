"""Fork LSST repos into a showow GitHub organization."""


import argparse
import textwrap
import os
from time import sleep
import progressbar
from .. import codetools


def parse_args():
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
    return parser.parse_args()


def main():
    args = parse_args()

    if args.debug:
        print 'You are', args.user

    gh = codetools.login_github(token_path=args.token_path)

    # get the organization object
    organization = gh.organization('lsst')

    # list of all LSST repos
    repos = [g for g in organization.repositories()]
    repo_count = len(repos)

    if args.debug:
        print repos

    widgets = ['Forking: ', progressbar.Bar(), ' ', progressbar.AdaptiveETA()]
    bar = progressbar.ProgressBar(
        widgets=widgets, max_value=repo_count).start()
    repo_idx = 0
    for repo in repos:
        if args.debug:
            print repo.name

        forked_repo = repo.create_fork(args.shadow_org)  # NOQA
        sleep(2)
        bar.update(repo_idx)
        repo_idx = repo_idx + 1

        # forked_name = forked_repo.name
        # Trap previous fork with dm_ prefix
        # if not forked_name.startswith("dm_"):
        #     newname = "dm_" + forked_name
        #     forked_repo.edit(newname)

if __name__ == '__main__':
    main()
