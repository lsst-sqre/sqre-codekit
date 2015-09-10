"""
Module for assorted codetools scripts
"""

# technical debt
# --------------
# - package
# - exception rather than sysexit
# - check explictly for github3 version
# major API breakage between
# github3.py                 - Python wrapper for the GitHub API(http://developer.github.com/v3)
#  INSTALLED: 0.9.4
#  LATEST:    1.0.0a1



from github3 import login
import urllib3
import os, re
import sys

def github(authfile='~/.github_token'):

    """
    returns a github login token
    """
    
    mytoken = None
    file_credential = os.path.expanduser(authfile)

    if not os.path.isfile(file_credential):
        print "You don't have a token in {0} ".format(file_credential)
        print "Have you run github_auth.py?"
        sys.exit(1)

    with open(file_credential, 'r') as fd:
        mytoken = fd.readline().strip()
            
    gh = login(token=mytoken)

    return(gh)

def eups2git_ref(eups_ref,
                 repo,
                 eupsbuild,
                 versiondb = 'https://raw.githubusercontent.com/lsst/versiondb/master/manifests',
                 debug = None):
    
    """
    Given an eups tag (master-g3b482c0804 or v10_0) give back the git ref (3b482c0804)
    """

    # Thought of trying to parse the eups tag for the ref, but given
    # that doesn't help with the tag-based versions, might as well
    # look up versiondb for everything

    # eg. https://raw.githubusercontent.com/lsst/versiondb/master/manifests/b1108.txt
    shafile = versiondb + '/' + eupsbuild + '.txt'
    if debug: print shafile

        # Get the file tying shas to eups versions
    http = urllib3.PoolManager()
    refs = http.request('GET', shafile)
    if refs.status >= 300: raise RuntimeError("Failed GET with HTTP code",refs.status)
    reflines = refs.data.splitlines()

    found = False
    for entry in reflines:
        # skip commented out and blank lines
        if entry.startswith('#'): continue
        if entry.startswith('BUILD'): continue
        if entry == '': continue
        
        elements = entry.split()
        eupspkg, sha, eupsver = elements[0], elements[1], elements[2]
        if eupspkg != repo: continue
        # sanity check
        if eupsver != eups_ref:
            raise RuntimeError('Something has gone wrong, release file does not match manifest', eups_ref, eupsver)
        # get out if we find it
        if debug: print eupspkg, sha, eupsver
        break

    return(sha)

            



        
        


    

    
    

