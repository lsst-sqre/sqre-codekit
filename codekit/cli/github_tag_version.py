#!/usr/bin/env python3
"""
Use URL to EUPS candidate tag file to git tag repos with official version
"""

# Technical Debt
# --------------
# - completely hide eups-specifics from this file
# - support repos.yaml for github repo resolution
# - worth doing the smart thing for externals? (yes for Sims)
# - deal with authentication version

# Known Bugs
# ----------
# Yeah, the candidate logic is broken, will fix


from .. import codetools
from .. import debug, warn, error
import argparse
import codekit.pygithub as pygithub
import copy
import github
import logging
import os
import requests
import sys
import textwrap

logging.basicConfig()
logger = logging.getLogger('codekit')
eupspkg_site = 'https://eups.lsst.codes/stack/src'


class GitTagExistsError(Exception):
    pass


def parse_args():
    """Parse command-line arguments"""

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

    parser.add_argument('tag')
    parser.add_argument('manifest')
    parser.add_argument(
        '--org',
        required=True,
        help="Github organization")
    parser.add_argument(
        '--team',
        action='append',
        required=True,
        help="team whose repos may be tagged (can specify several times")
    parser.add_argument('--candidate')
    parser.add_argument('--dry-run', action='store_true')
    parser.add_argument(
        '--user',
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
    parser.add_argument('-v', '--version', action=codetools.ScmVersionAction)
    return parser.parse_args()


def cmp_dict(d1, d2, ignore_keys=[]):
    """Compare dicts ignoring select keys"""
    # https://stackoverflow.com/questions/10480806/compare-dictionaries-ignoring-specific-keys
    return {k: v for k, v in d1.items() if k not in ignore_keys} \
        == {k: v for k, v in d2.items() if k not in ignore_keys}


def fetch_eups_tag_file(args, eups_candidate):
    # construct url
    eupspkg_taglist = '/'.join((eupspkg_site, 'tags',
                                eups_candidate + '.list'))
    debug("fetching: {url}".format(url=eupspkg_taglist))

    r = requests.get(eupspkg_taglist)
    r.raise_for_status()

    return r.text


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


def eups_products_to_gh_repos(
    org,
    teams,
    eupsbuild,
    eups_products,
    debug=False
):
    gh_repos = []

    for prod in eups_products:
        codetools.debug("looking for git repo for: {prod} [{ver}]".format(
            prod=prod['name'],
            ver=prod['eups_version']
        ))

        repo = org.get_repo(prod['name'])

        codetools.debug("  found: {slug}".format(slug=repo.full_name))

        repo_teams = [t.name for t in repo.get_teams()]
        if not any(x in repo_teams for x in teams):
            warn(textwrap.dedent("""\
                No action for {repo}
                  has teams: {repo_teams}
                  does not belong to any of: {tag_teams}\
                """).format(
                repo=repo.full_name,
                repo_teams=repo_teams,
                tag_teams=teams,
            ))
            continue

        sha = codetools.eups2git_ref(
            product=repo.name,
            eups_version=prod['eups_version'],
            build_id=eupsbuild,
            debug=debug
        )

        gh_repos.append({
            'repo': repo,
            'product': prod['name'],
            'eups_version': prod['eups_version'],
            'sha': sha,
        })

    return gh_repos


def author_to_dict(obj):
    """Who needs a switch/case statement when you can instead use this easy to
    comprehend drivel?
    """
    def default():
        raise RuntimeError("unsupported type {t}".format(t=type(obj).__name__))

    # a more pythonic way to handle this would be several try blocks to catch
    # missing attributes
    return {
        # GitAuthor has name,email,date properties
        'GitAuthor': lambda x: {'name': x.name, 'email': x.email},
        # InputGitAuthor only has _identity, which returns a dict
        'InputGitAuthor': lambda x: x._identity,
    }.get(type(obj).__name__, lambda x: default())(obj)


def cmp_gitauthor(a, b):
    # ignore date
    if cmp_dict(author_to_dict(a), author_to_dict(b), ['date']):
        return True

    return False


def cmp_existing_git_tag(t_tag, e_tag):
    assert isinstance(t_tag, dict)
    assert isinstance(e_tag, github.GitTag.GitTag)

    # ignore date when comparing tag objects
    if t_tag['sha'] == e_tag.object.sha and \
       t_tag['message'] == e_tag.message and \
       cmp_gitauthor(t_tag['tagger'], e_tag.tagger):
        return True

    return False


def check_existing_git_tag(repo, t_tag):
    """
    Check for a pre-existng tag in the github repo.

    Parameters
    ----------
    repo : dict
        dict representing a target github repo
    t_tag: dict
        dict repesenting a target git tag

    Returns
    -------
    insync : `bool`
        True if tag exists and is in sync. False if tag does not exist.

    Raises
    ------
    GitTagExistsError
        If tag exists but is not in sync.
    """

    debug("looking for existing tag: {tag}"
          .format(tag=t_tag['name']))

    # find ref/tag by name
    e_ref = pygithub.find_tag_by_name(repo['repo'], t_tag['name'])
    if not e_ref:
        debug("  not found: {tag}".format(tag=t_tag['name']))
        return False

    # find tag object pointed to by the ref
    e_tag = repo['repo'].get_git_tag(e_ref.object.sha)
    debug("  found existing tag: {tag}".format(tag=e_tag))

    if cmp_existing_git_tag(t_tag, e_tag):
        return True

    warn(textwrap.dedent("""\
        tag {tag} already exists with conflicting values:
          existing:
            sha: {e_sha}
            message: {e_message}
            tagger: {e_tagger}
          target:
            sha: {t_sha}
            message: {t_message}
            tagger: {t_tagger}\
    """).format(
        tag=t_tag['name'],
        e_sha=e_tag['sha'],
        e_message=e_tag['message'],
        e_tagger=e_tag['tagger'],
        t_sha=t_tag['sha'],
        t_message=t_tag['message'],
        t_tagger=t_tag['tagger'],
    ))

    raise GitTagExistsError("tag {tag} alreaday exists"
                            .format(tag=e_tag))


def tag_gh_repos(gh_repos, args, tag_template):
    tag_exceptions = []
    for repo in gh_repos:
        # "target tag"
        t_tag = copy.copy(tag_template)
        t_tag['sha'] = repo['sha']

        # control whether to create a new tag or update an existing one
        update_tag = False

        debug(textwrap.dedent("""\
            tagging repo: {repo}
              sha: {sha} as {gt}
              (eups version: {et})\
            """).format(
            repo=repo['repo'].full_name,
            sha=t_tag['sha'],
            gt=t_tag['name'],
            et=repo['eups_version']
        ))

        try:
            # if the existing tag is in sync, do nothing
            if check_existing_git_tag(repo, t_tag):
                warn(textwrap.dedent("""\
                    No action for {repo}
                      existing tag: {tag} is already in sync\
                    """).format(
                    repo=repo['repo'].full_name,
                    tag=t_tag['name'],
                ))

                continue
        except GitTagExistsError as e:
            yikes = pygithub.CaughtRepositoryError(repo['repo'], e)

            if args.force_tag:
                update_tag = True
            elif args.fail_fast:
                raise yikes from None
            else:
                tag_exceptions.append(yikes)
                continue

        # tags are created/updated past this point
        if args.dry_run:
            continue

        try:
            tag_obj = repo['repo'].create_git_tag(
                t_tag['name'],
                t_tag['message'],
                t_tag['sha'],
                'commit',
                tagger=t_tag['tagger'],
            )
            debug("  created tag object {tag_obj}".format(tag_obj=tag_obj))

            if update_tag:
                ref = pygithub.find_tag_by_name(
                    repo['repo'],
                    t_tag['name'],
                    safe=False
                )
                ref.edit(tag_obj.sha, force=True)
                debug("  updated existing ref: {ref}".format(ref=ref))
            else:
                ref = repo['repo'].create_git_ref(
                    "refs/tags/{t}".format(t=t_tag['name']),
                    tag_obj.sha
                )
                debug("  created ref: {ref}".format(ref=ref))
        except Exception as e:
            yikes = pygithub.CaughtRepositoryError(repo['repo'], e)
            if args.fail_fast:
                raise yikes from None
            tag_exceptions.append(yikes)
            error(yikes)

    lp_fires = len(tag_exceptions)
    if lp_fires:
        error("ERROR: {failed} tag failures".format(failed=str(lp_fires)))

        for e in tag_exceptions:
            error(e)

        sys.exit(lp_fires if lp_fires < 256 else 255)


def main():
    """Create the tag"""

    args = parse_args()

    if args.debug:
        logger.setLevel(logging.DEBUG)

    version = args.tag

    # if email not specified, try getting it from the gitconfig
    git_email = codetools.lookup_email(args)
    # ditto for the name of the git user
    git_user = codetools.lookup_user(args)

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

    tagger = github.InputGitAuthor(
        git_user,
        git_email,
        codetools.current_timestamp()
    )
    debug(tagger)

    # all tags should be the same across repos -- just add the 'sha' key and
    # stir
    tag_template = {
        'name': version,
        'message': message,
        'tagger': tagger,
    }

    debug(tag_template)

    g = pygithub.login_github(token_path=args.token_path, token=args.token)
    org = g.get_organization(args.org)
    debug("tagging repos in github org: {org}".format(org=org.login))

    # generate eups-style version
    # eups no likey semantic versioning markup, wants underscores
    cmap = str.maketrans('.-', '__')
    eups_candidate = candidate.translate(cmap)

    manifest = fetch_eups_tag_file(args, eups_candidate)
    eups_products = parse_eups_tag_file(manifest)

    gh_repos = eups_products_to_gh_repos(
        org,
        args.team,
        eupsbuild,
        eups_products,
        args.debug
    )
    tag_gh_repos(gh_repos, args, tag_template)


if __name__ == '__main__':
    main()
