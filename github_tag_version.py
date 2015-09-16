#!/usr/bin/env python

"""
Use URL to EUPS candidate tag file to git tag repos with official version
"""

# Technical Debt
# --------------
# - sort out the certificate so we don't have to supress warnings
# - completely hide eups-specifics from this file
# - skips non-github repos - can add repos.yaml knowhow to address this
# - worth doing the smart thing for externals? (yes for Sims)
# - deal with authentication version

# Known Bugs
# ----------
# Yeah, the candidate logic is broken, will fix

import codetools
import urllib3
import webbrowser
import os
import sys
import argparse
import textwrap
from time import sleep
from datetime import datetime
from getpass import getuser
from string import maketrans

debug = os.getenv("DM_SQUARE_DEBUG")
trace = False
user = getuser()

# argument parsing and default options

parser = argparse.ArgumentParser(
    prog='github_tag_version',
    formatter_class=argparse.RawDescriptionHelpFormatter,
    description=textwrap.dedent('''

    Tag all repositories in a Github org using a team-based scheme

    Examples:
    github_tag_version.py --org lsst w.2015.33 b1630

    github_tag_version.py --org lsst --candidate v11_0_rc2 11.0.rc2 b1679

    '''),
    epilog='Part of codekit: https://github.com/lsst-sqre/sqre-codekit'
)

# for safety, default to dummy org
# will fail for most people but see github_fork_repos in this module
# on how to get your own

parser.add_argument('tag')

parser.add_argument('manifest')

parser.add_argument('--org',
                    default=user+'-shadow')

parser.add_argument('--sims')

parser.add_argument('--candidate')

parser.add_argument('--dry-run', action='store_true')

parser.add_argument('-v', '--version', action='version', version='%(prog)s 0.5')

opt = parser.parse_args()


# we'll pass those as args later (see TD)
orgname = opt.org
version = opt.tag

# The candidate is assumed to be the requested EUPS tag unless
# otherwise specified with the --candidate option The reason to
# currently do this is that for weeklies and other internal builds,
# it's okay to eups publish the weekly and git tag post-facto. However
# for official releases, we don't want to publish until the git tag
# goes down, because we want to eups publish the build that has the
# official versions in the eups ref.

if opt.candidate:
    candidate = opt.candidate
else:
    candidate = opt.tag

eupsbuild = opt.manifest # sadly we need to "just" know this
message = 'Version ' + version + ' release from ' + candidate +'/'+eupsbuild
eupspkg_site = 'https://sw.lsstcorp.org/eupspkg/'

# generate timestamp for github API
now = datetime.utcnow()
timestamp = now.isoformat()[0:19]+'Z'
if debug: print(timestamp)

tagger = dict(name = user,
              email = user + '@lsst.org',
              date = timestamp)

if debug: print tagger

gh = codetools.github(authfile='~/.sq_github_token_delete')
if debug: print(type(gh))

org = gh.organization(orgname)
if debug: print("Tagging repos in ",orgname)

# generate eups-style version
# eups no likey semantic versioning markup, wants underscores

map = maketrans('.-','__')

eups_version = version.translate(map)
eups_candidate = candidate.translate(map)

# construct url
eupspkg_taglist = '/'.join((eupspkg_site, 'tags', eups_candidate + '.list'))
if debug: print eupspkg_taglist

http = urllib3.PoolManager()
# supress the certificate warning - technical debt
urllib3.disable_warnings()
if trace:
    import logging
    urllib3 = logging.getLogger('requests.packages.urllib3')
    stream_handler = logging.StreamHandler()
    logger = logging.getLogger('github3')
    logger.addHandler(stream_handler)
    logger.setLevel(logging.DEBUG)

manifest = http.request('GET', eupspkg_taglist)

if manifest.status >= 300: sys.exit("Failed GET")

entries = manifest.data.split('\n')

for entry in entries:
    # skip commented out and blank lines
    if entry.startswith('#'): continue
    if entry.startswith('EUPS'): continue
    if entry == '': continue

    # extract the repo and eups tag from the entry
    (upstream, generic, eups_tag) = entry.split()
    if debug: print upstream, eups_tag

    # okay so we still have the data dirs on gitolite
    # for now, just skip them and record them.
    # question is should they be on different tagging scheme anyway?
    # at this point these are: afwdata, astrometry_net_data qserv_testdata

    repo = gh.repository(orgname, upstream)

    # if the repo is not in github skip it for now
    # see TD
    if not hasattr(repo, 'name'):
        print '!!! SKIPPING', upstream, (60-len(upstream)) * '-'
        continue

    for team in repo.iter_teams():
        if team.name == 'Data Management':
            if debug or opt.dry_run:
                print repo.name.ljust(40), 'found in', team.name
            sha = codetools.eups2git_ref(eups_ref = eups_tag, repo = repo.name, eupsbuild = eupsbuild, debug = debug)
            if debug or opt.dry_run:
                print 'Will tag sha:',sha, 'as', version, '(was',eups_tag,')'


            if not opt.dry_run:
                backtag = repo.create_tag(tag = version,
                                          message = message,
                                          sha = sha,
                                          obj_type = 'commit',
                                          tagger = tagger,
                                          lightweight = False)

        elif team.name == 'DM External':
            if debug: print repo.name, 'found in', team.name
        else:
            if debug: print 'No action for', repo.name, 'belonging to', team.name

