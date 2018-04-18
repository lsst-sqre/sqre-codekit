#!/usr/bin/env python3
"""
Use URL to EUPS candidate tag file to git tag repos with official version
"""

# Technical Debt
# --------------
# - completely hide eups-specifics from this file
# - skips non-github repos - can add repos.yaml knowhow to address this
# - worth doing the smart thing for externals? (yes for Sims)
# - deal with authentication version

# Known Bugs
# ----------
# Yeah, the candidate logic is broken, will fix


import logging
import os
import sys
import argparse
import textwrap
from datetime import datetime
from getpass import getuser
import certifi
import urllib3
import copy
from .. import codetools
from .. import debug, warn, error

logging.basicConfig()
logger = logging.getLogger('codekit')
eupspkg_site = 'https://eups.lsst.codes/stack/src'


class CaughtGitError(Exception):
    def __init__(self, repo, caught):
        self.repo = repo
        self.caught = caught

    def __str__(self):
        return textwrap.dedent("""\
            Caught: {name}
              In repo: {repo}
              Message: {e}\
            """.format(
            name=type(self.caught),
            repo=self.repo,
            e=str(self.caught)
        ))


def lookup_email(args):
    email = args.email
    if email is None:
        email = codetools.gituseremail()
        if email is None:
            sys.exit("Specify --email option")

    debug("email is " + email)

    return email


def lookup_tagger(args):
    tagger = args.tagger
    if tagger is None:
        tagger = codetools.gitusername()
        if tagger is None:
            sys.exit("Specify --tagger option")

    debug("tagger name is " + tagger)

    return tagger


def current_timestamp(args):
    now = datetime.utcnow()
    timestamp = now.isoformat()[0:19] + 'Z'

    debug("generated timestamp: {now}".format(now=timestamp))

    return timestamp


def fetch_eups_tag_file(args, eups_candidate):
    # construct url
    eupspkg_taglist = '/'.join((eupspkg_site, 'tags',
                                eups_candidate + '.list'))
    debug("fetching: {url}".format(url=eupspkg_taglist))

    http = urllib3.PoolManager(
        cert_reqs='CERT_REQUIRED',
        ca_certs=certifi.where()
    )

    manifest = http.request('GET', eupspkg_taglist)

    if manifest.status >= 300:
        sys.exit("Failed GET")

    return manifest.data


def parse_eups_tag_file(data):
    products = []

    for line in data.splitlines():
        if not isinstance(line, str):
            line = str(line, 'utf-8')
        # skip commented out and blank lines
        if line.startswith('#'):
            continue
        if line.startswith('EUPS'):
            continue
        if line == '':
            continue

        # extract the repo and eups tag
        (product, _, eups_version) = line.split()[0:3]

        products.append({
            'name': product,
            'eups_version': eups_version,
        })

    return products


def eups_products_to_gh_repos(args, ghb, orgname, eupsbuild, eups_products):
    gh_repos = []

    for prod in eups_products:
        debug("looking for git repo for: {prod} {ver}".format(
            prod=prod['name'],
            ver=prod['eups_version']
        ))

        repo = ghb.repository(orgname, prod['name'])

        # if the repo is not in github skip it for now
        # see TD
        if not hasattr(repo, 'name'):
            error("!!! unable to resolve github repo for product: {name}"
                  .format(name=prod['name']))
            continue

        debug("  found: {slug}".format(slug=repo))

        repo_teams = [t.name for t in repo.teams()]
        if not any(x in repo_teams for x in args.team):
            warn(textwrap.dedent("""\
                No action for {repo}
                  has teams: {repo_teams}
                  does not belong to any of: {tag_teams}\
                """).format(
                repo=repo,
                repo_teams=repo_teams,
                tag_teams=args.team,
            ))
            continue

        sha = codetools.eups2git_ref(
            product=repo.name,
            eups_version=prod['eups_version'],
            build_id=eupsbuild,
            debug=args.debug
        )

        gh_repos.append({
            'repo': repo,
            'product': prod['name'],
            'eups_version': prod['eups_version'],
            'sha': sha,
        })

    return gh_repos


def tag_gh_repos(gh_repos, args, tag_template):
    tag_exceptions = []
    for repo in gh_repos:
        # "target tag"
        t_tag = copy.copy(tag_template)
        t_tag['sha'] = repo['sha']

        debug(textwrap.dedent("""\
            tagging repo: {repo}
              sha: {sha} as {gt}
              (eups version: {et})\
            """).format(
            repo=repo['repo'],
            sha=t_tag['sha'],
            gt=t_tag['name'],
            et=repo['eups_version']
        ))

        if args.dry_run:
            continue

        try:
            # create_tag() returns a Tag object on success or None
            # on failure
            tag = repo['repo'].create_tag(
                tag=t_tag['name'],
                message=t_tag['message'],
                sha=t_tag['sha'],
                obj_type='commit',
                tagger=t_tag['tagger'],
                lightweight=False,
                update=args.force_tag
            )
            if tag is None:
                raise RuntimeError('failed to create git tag')

        except Exception as e:
            yikes = CaughtGitError(repo['repo'], e)
            tag_exceptions.append(yikes)
            error(yikes)

            if args.fail_fast:
                raise yikes

    lp_fires = len(tag_exceptions)
    if lp_fires:
        error("ERROR: {failed} tag failures".format(failed=str(lp_fires)))

        for e in tag_exceptions:
            error(e)

        sys.exit(lp_fires if lp_fires < 256 else 255)


def parse_args():
    """Parse command-line arguments"""
    user = getuser()

    parser = argparse.ArgumentParser(
        prog='github-tag-version',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        description=textwrap.dedent("""

        Tag all repositories in a GitHub org using a team-based scheme

        Examples:
        github-tag-version --org lsst --team 'Data Management' w.2015.33 b1630

        github-tag-version --org lsst --team 'Data Management' \
            --team 'External' --candidate v11_0_rc2 11.0.rc2 b1679

        Note that the access token must have access to these oauth scopes:
            * read:org
            * repo

        The token generated by `github-auth --user` should have sufficient
        permissions.
        """),
        epilog='Part of codekit: https://github.com/lsst-sqre/sqre-codekit'
    )

    # for safety, default to dummy org <user>-shadow
    # will fail for most people but see github_fork_repos in this module
    # on how to get your own

    parser.add_argument('tag')
    parser.add_argument('manifest')
    parser.add_argument(
        '--org',
        default=user + '-shadow')
    parser.add_argument(
        '--team',
        action='append',
        required=True,
        help="team whose repos may be tagged (can specify several times")
    parser.add_argument('--candidate')
    parser.add_argument('--dry-run', action='store_true')
    parser.add_argument(
        '--tagger',
        help='Name of person making the tag - defaults to gitconfig value')
    parser.add_argument(
        '--email',
        help='Email address of tagger - defaults to gitconfig value')
    parser.add_argument(
        '--token-path',
        default='~/.sq_github_token_delete',
        help='Use a token (made with github-auth) in a non-standard location')
    parser.add_argument(
        '--token',
        default=None,
        help='Literal github personal access token string')
    parser.add_argument(
        '--force-tag',
        action='store_true',
        help='Force moving pre-existing annotated git tags.')
    parser.add_argument(
        '--fail-fast',
        action='store_true',
        help='Fail immediately on github API errors.')
    parser.add_argument(
        '-d', '--debug',
        action='store_true',
        default=os.getenv('DM_SQUARE_DEBUG'),
        help='Debug mode')
    parser.add_argument('-v', '--version',
                        action='version', version='%(prog)s 0.5')
    return parser.parse_args()


def main():
    """Create the tag"""

    args = parse_args()

    if args.debug:
        logger.setLevel(logging.DEBUG)

    orgname = args.org
    version = args.tag

    # if email not specified, try getting it from the gitconfig
    email = lookup_email(args)
    # ditto for the name of the tagger
    tagger_name = lookup_tagger(args)

    # The candidate is assumed to be the requested EUPS tag unless
    # otherwise specified with the --candidate option The reason to
    # currently do this is that for weeklies and other internal builds,
    # it's okay to eups publish the weekly and git tag post-facto. However
    # for official releases, we don't want to publish until the git tag
    # goes down, because we want to eups publish the build that has the
    # official versions in the eups ref.
    candidate = args.candidate if args.candidate else args.tag

    eupsbuild = args.manifest  # sadly we need to "just" know this
    message_template = 'Version {v} release from {c}/{b}'
    message = message_template.format(v=version, c=candidate, b=eupsbuild)

    # generate timestamp for github API
    timestamp = current_timestamp(args)

    # all tags should be the same across repos -- just add the 'sha' key and
    # stir
    tag_template = {
        'name': version,
        'message': message,
        'tagger': {
            'name': tagger_name,
            'email': email,
            'date': timestamp,
        }
    }

    debug(tag_template)

    ghb = codetools.login_github(token_path=args.token_path, token=args.token)

    debug("Tagging repos in github org: {org}".format(org=orgname))

    # generate eups-style version
    # eups no likey semantic versioning markup, wants underscores
    cmap = str.maketrans('.-', '__')
    eups_candidate = candidate.translate(cmap)

    manifest = fetch_eups_tag_file(args, eups_candidate)
    eups_products = parse_eups_tag_file(manifest)
    gh_repos = eups_products_to_gh_repos(
        args,
        ghb,
        orgname,
        eupsbuild,
        eups_products
    )
    tag_gh_repos(gh_repos, args, tag_template)


if __name__ == '__main__':
    main()
