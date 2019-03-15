#!/usr/bin/env python3

from codekit.codetools import debug, error, info, warn
from codekit import codetools, pygithub
from time import sleep
import argparse
import codekit.progressbar as pbar
import github
import itertools
import sys
import textwrap


def parse_args():
    """Parse command-line arguments"""
    prog = 'github-decimate-org'

    parser = argparse.ArgumentParser(
        prog=prog,
        formatter_class=argparse.RawDescriptionHelpFormatter,
        description=textwrap.dedent("""
            Delete repos and/or teams from a GitHub organization.

            Example:

                {prog} \\
                    --dry-run \\
                    --debug \\
                    --org 'example' \\
                    --token "$GITHUB_TOKEN" \\
                    --delete-repos \\
                    --delete-repos-limit 3 \\
                    --delete-teams \\
                    --delete-teams-limit 3

        """).format(prog=prog),
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
        '--delete-repos',
        action='store_true',
        help='Delete *ALL* repos in org')
    parser.add_argument(
        '--delete-repos-limit',
        default=None,
        type=int,
        help='Maximum number of repos to delete')
    parser.add_argument(
        '--delete-teams',
        action='store_true',
        help='Delete *ALL* teams in org')
    parser.add_argument(
        '--delete-teams-limit',
        default=None,
        type=int,
        help='Maximum number of teams to delete')
    parser.add_argument('--dry-run', action='store_true')
    parser.add_argument(
        '--fail-fast',
        action='store_true',
        help='Fail immediately on github API errors.')
    parser.add_argument(
        '--no-fail-fast',
        action='store_const',
        const=False,
        dest='fail_fast',
        help='DO NOT Fail immediately on github API errors. (default)')
    parser.add_argument(
        '-d', '--debug',
        action='count',
        default=codetools.debug_lvl_from_env(),
        help='Debug mode (can specify several times)')
    parser.add_argument('-v', '--version', action=codetools.ScmVersionAction)
    return parser.parse_args()


def delete_all_repos(org, **kwargs):
    assert isinstance(org, github.Organization.Organization), type(org)
    limit = kwargs.pop('limit', None)

    try:
        repos = list(itertools.islice(org.get_repos(), limit))
    except github.RateLimitExceededException:
        raise
    except github.GithubException as e:
        msg = 'error getting repos'
        raise pygithub.CaughtOrganizationError(org, e, msg) from None

    info("found {n} repos in {org}".format(n=len(repos), org=org.login))
    [debug("  {r}".format(r=r.full_name)) for r in repos]

    if repos:
        warn("Deleting all repos in {org}".format(org=org.login))
        pbar.wait_for_user_panic_once()

    return delete_repos(repos, **kwargs)


def delete_repos(repos, fail_fast=False, dry_run=False, delay=0):
    assert isinstance(repos, list), type(repos)

    problems = []
    for r in repos:
        assert isinstance(r, github.Repository.Repository), type(r)

        if delay:
            sleep(delay)

        try:
            info("deleting: {r}".format(r=r.full_name))
            if dry_run:
                info('  (noop)')
                continue
            r.delete()
        except github.RateLimitExceededException:
            raise
        except github.GithubException as e:
            msg = 'FAILED - does your token have delete_repo scope?'
            yikes = pygithub.CaughtRepositoryError(r, e, msg)
            if fail_fast:
                raise yikes from None
            problems.append(yikes)
            error(yikes)

    return problems


def delete_all_teams(org, **kwargs):
    assert isinstance(org, github.Organization.Organization), type(org)
    limit = kwargs.pop('limit', None)

    try:
        teams = list(itertools.islice(org.get_teams(), limit))
    except github.RateLimitExceededException:
        raise
    except github.GithubException as e:
        msg = 'error getting teams'
        raise pygithub.CaughtOrganizationError(org, e, msg) from None

    info("found {n} teams in {org}".format(n=len(teams), org=org.login))
    [debug("  '{t}'".format(t=t.name)) for t in teams]

    if teams:
        warn("Deleting all teams in {org}".format(org=org.login))
        pbar.wait_for_user_panic_once()

    return delete_teams(teams, **kwargs)


def delete_teams(teams, fail_fast=False, dry_run=False, delay=0):
    assert isinstance(teams, list), type(teams)

    problems = []
    for t in teams:
        if delay:
            sleep(delay)

        try:
            info("deleting team: '{t}'".format(t=t.name))
            if dry_run:
                info('  (noop)')
                continue
            t.delete()
        except github.RateLimitExceededException:
            raise
        except github.GithubException as e:
            yikes = pygithub.CaughtTeamError(t, e)
            if fail_fast:
                raise yikes from None
            problems.append(yikes)
            error(yikes)

    return problems


def run():
    args = parse_args()

    codetools.setup_logging(args.debug)

    global g
    g = pygithub.login_github(token_path=args.token_path, token=args.token)
    codetools.validate_org(args.org)
    org = g.get_organization(args.org)

    # list of exceptions
    problems = []

    if args.delete_repos:
        problems += delete_all_repos(
            org,
            fail_fast=args.fail_fast,
            limit=args.delete_repos_limit,
            dry_run=args.dry_run
        )

    if args.delete_teams:
        problems += delete_all_teams(
            org,
            fail_fast=args.fail_fast,
            limit=args.delete_teams_limit,
            dry_run=args.dry_run
        )

    if problems:
        msg = "{n} errors removing repo(s)/teams(s)".format(
            n=len(problems))
        raise codetools.DogpileError(problems, msg)

    info("Consider deleting your privileged auth token @ {path}".format(
        path=args.token_path))


def main():
    try:
        try:
            run()
        except codetools.DogpileError as e:
            error(e)
            n = len(e.errors)
            sys.exit(n if n < 256 else 255)
        else:
            sys.exit(0)
        finally:
            if 'g' in globals():
                pygithub.debug_ratelimit(g)
    except SystemExit as e:
        debug("exit {status}".format(status=str(e)))
        raise e


if __name__ == '__main__':
    main()
