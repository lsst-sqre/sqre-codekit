#!/usr/bin/env python

"""
Use URL to EUPS candidate tag file to git tag repos with official version
"""

# Technical Debt
# --------------
# - sort out the certificate so we don't have to supress warnings
# - completely hide eups-specifics from this file

import codetools
import urllib3
import webbrowser
import os, sys
from time import sleep

debug = os.getenv("DM_SQUARE_DEBUG")

version = '10.1'
candidate = '10.1.rc3'
eupspkg_site = 'https://sw.lsstcorp.org/eupspkg/'
orgname = 'frossie-shadow'

gh = codetools.github(authfile='~/.sq_github_token_delete')
if debug: print(type(gh))

org = gh.organization(orgname)

# generate eups-style version
eups_version = codetools.git2eups_version(git_version=version)
eups_candidate = codetools.git2eups_version(git_version=candidate)

if debug: print eups_version

# construct url
eupspkg_taglist = '/'.join((eupspkg_site, 'tags', eups_candidate + '.list'))
if debug: print eupspkg_taglist

http = urllib3.PoolManager()
# supress the certificate warning - technical debt
urllib3.disable_warnings()
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

    if not hasattr(repo, 'name'):
        print '!!! SKIPPING', upstream, (60-len(upstream)) * '-'
        continue


        

    
    


    





