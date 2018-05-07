#!/usr/bin/env python3
"""Delete all repos in the Github <user>-shadow org."""
import textwrap
import argparse
import os
from time import sleep
import progressbar
from .. import codetools


def parse_args():
    """Parse command-line arguments"""
    parser = argparse.ArgumentParser(
        prog='github-delete-shadow',
        description=textwrap.dedent("""Delete all repos in the GitHub
            <username>-shadow org"""),
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog='Part of codekit: https://github.com/lsst-sqre/sqre-codekit')
    parser.add_argument(
        '-u', '--user',
        help='GitHub username',
        dest='user',
        required=True)
    parser.add_argument(
        '--token-path',
        default='~/.sq_github_token_delete',
        help='Use a token (made with github-auth) in a non-standard loction')
    parser.add_argument(
        '-d', '--debug',
        action='store_true',
        default=os.getenv('DM_SQUARE_DEBUG'),
        help='Debug mode')
    parser.add_argument('-v', '--version', action=codetools.ScmVersionAction)
    return parser.parse_args()


def countdown_timer():
    """Show countdown bar"""
    widgets = ['Pause for panic: ', progressbar.ETA(), ' ', progressbar.Bar()]
    pbar = progressbar.ProgressBar(widgets=widgets, max_value=200).start()
    for i in range(200):
        pbar.update(i)
        sleep(0.1)
    pbar.finish()


def main():
    """Delete user shadow org"""
    work = 0
    nowork = 0

    args = parse_args()
    # Deliberately hardcoding the -shadow part due to cowardice
    orgname = '{user}-shadow'.format(user=args.user)

    if args.debug:
        print('org:', orgname)

    ghb = codetools.login_github(token_path=args.token_path)

    # get the organization object
    organization = ghb.organization(orgname)

    # get all the repos
    repos = [g for g in organization.repositories()]

    print('Deleting all repos in', orgname)
    print('Now is the time to panic and Ctrl-C')

    countdown_timer()

    print('Here goes:')

    if args.debug:
        delay = 5
        print(delay, 'second gap between deletions')
        work = 0
        nowork = 0

    for repo in repos:

        if args.debug:
            print('Next deleting:', repo.name, '...',)
            sleep(delay)

        status = repo.delete()

        if status:
            print('ok')
            work += 1
        else:
            print('FAILED - does your token have delete_repo scope?')
            nowork += 1

    print('Done - Succeed:', work, 'Failed:', nowork)
    if work:
        print('Consider deleting your privileged auth token', args.token_path)


if __name__ == '__main__':
    main()
