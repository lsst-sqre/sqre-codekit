#!/usr/bin/env python3
"""Delete all repos in the Github <user>-shadow org."""

from codekit.codetools import debug, error, info, warn
from codekit import codetools
from codekit import pygithub
from time import sleep
import argparse
import github
import itertools
import logging
import os
import progressbar
import sys
import textwrap

logging.basicConfig()
logger = logging.getLogger('codekit')


def parse_args():
    """Parse command-line arguments"""
    parser = argparse.ArgumentParser(
        prog='github-delete-shadow',
        description=textwrap.dedent("""Delete all repos in the GitHub
            <username>-shadow org"""),
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog='Part of codekit: https://github.com/lsst-sqre/sqre-codekit')
    parser.add_argument(
        '--org',
        required=True,
        help='GitHub Organization')
    parser.add_argument(
        '--token-path',
        default='~/.sq_github_token_delete',
        help='Use a token (made with github-auth) in a non-standard loction')
    parser.add_argument(
        '--token',
        default=None,
        help='Literal github personal access token string')
    parser.add_argument(
        '--limit',
        default=None,
        type=int,
        help='Maximum number of repos to delete')
    parser.add_argument(
        '--delete-teams',
        action='store_true',
        help='Delete *ALL* teams in org in addition to removing repos')
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


def delete_all_teams(org, **kwargs):
    assert isinstance(org, github.Organization.Organization), type(org)
    limit = kwargs.pop('limit', None)

    teams = list(itertools.islice(org.get_teams(), limit))
    # print full Org object as non-visible orgs will have a name of `None`
    info("found {n} teams in {org}".format(n=len(teams), org=org))
    [debug("  {t}".format(t=t)) for t in teams]

    return delete_teams(teams, **kwargs)


def delete_teams(teams, fail_fast=False, dry_run=False, delay=0):
    assert isinstance(teams, list), type(teams)

    problems = []
    for t in teams:
        if delay:
            sleep(delay)

        try:
            info("deleting team: {t}".format(t=t.name))
            if dry_run:
                debug('  (noop)')
                continue
            t.delete()
            info('OK')
        except github.GithubException as e:
            yikes = pygithub.CaughtTeamError(t, e)
            problems.append(yikes)
            error(yikes)

            if fail_fast:
                raise

    return problems


def main():
    args = parse_args()

    if args.debug:
        logger.setLevel(logging.DEBUG)

    g = pygithub.login_github(token_path=args.token_path, token=args.token)
    org = g.get_organization(args.org)

    # get all the repos
    repos = list(itertools.islice(org.get_repos(), args.limit))

    # print full Org object as non-visible orgs will have a name of `None`
    warn("Deleting all repos in {org}".format(org=org))
    warn('Now is the time to panic and Ctrl-C')

    countdown_timer()

    info('Here goes:')

    if args.debug:
        delay = 5
        debug("using a {d} second gap between deletions".format(d=delay))

    work = 0
    nowork = 0
    problems = []
    for r in repos:
        info("deleting: {r}".format(r=r.full_name))

        if args.debug:
            sleep(delay)

        try:
            r.delete()
            work += 1
            info('ok')
        except github.GithubException as e:
            yikes = pygithub.CaughtGitError(r, e)
            problems.append(yikes)
            nowork += 1
            error('FAILED - does your token have delete_repo scope?')
            error(yikes)

    info("Done - Succeed: {s} Failed: {n}".format(s=work, n=nowork))

    if args.delete_teams:
        problems += delete_all_teams(org)

    if problems:
        error("ERROR: {n} failures".format(n=str(len(problems))))

        for e in problems:
            error(e)

        sys.exit(1)

    if work:
        info("Consider deleting your privileged auth token @ {path}".format(
            path=args.token_path))


if __name__ == '__main__':
    main()
