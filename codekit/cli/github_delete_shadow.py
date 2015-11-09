"""Delete all repos in the Github <user>-shadow org."""

# (the -u in the commandline unbuffers output so the countdown works)

from getpass import getuser
import textwrap
import argparse
import os
from time import sleep
from .. import codetools


def parse_args():
    parser = argparse.ArgumentParser(
        prog='github-delete-shadow',
        description=textwrap.detent("""Delete all repos in the GitHub
            <username>-shadow org"""),
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog='Part of codekit: https://github.com/lsst-sqre/sqre-codekit')
    parser.add_argument(
        '-u', '--user', default=getuser(),
        help='GitHub username')
    parser.add_argument(
        '--token-path',
        default='~/.sq_github_token_delete',
        help='Use a token (made with github-auth) in a non-standard loction')
    parser.add_argument(
        '-d', '--debug',
        action='store_true',
        default=os.getenv('DM_SQUARE_DEBUG'),
        help='Debug mode')
    return parser.parse_args()


def main():
    args = parse_args()
    # Deliberately hardcoding the -shadow part due to cowardice
    orgname = '{user}-shadow'.format(user=args.user)

    if args.debug:
        print 'org:', orgname

    # file_credential = os.path.expanduser('~/.sq_github_token_delete')
    gh = codetools.github_login(token_path=args.token_path)

    # get the organization object
    organization = gh.organization(orgname)

    # get all the repos
    repos = [g for g in organization.iter_repos()]

    print 'Deleting all repos in', orgname
    print 'Now is the time to panic and Ctrl-C'

    secs = 10
    while secs >= 0:
        print secs, '...',
        sleep(2)
        secs -= 1

    print 'Here goes:'

    if args.debug:
        delay = 5
        print delay, 'second gap between deletions'
        work = 0
        nowork = 0

    for repo in repos:

        if args.debug:
            print 'Next deleting:', repo.name, '...',
            sleep(delay)

        status = repo.delete()

        if status:
            print 'ok'
            work += 1
        else:
            print 'FAILED - does your token have delete_repo scope?'
            nowork += 1

    print 'Done - Succeed:', work, 'Failed:', nowork
    if work:
        print 'Consider deleting your privileged auth token', args.token_path


if __name__ == '__main__':
    main()
