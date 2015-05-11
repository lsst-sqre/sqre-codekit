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

def git2eups_version(git_version):

    """
    Given a version string (10.1) generates an eups style version (v10_1)
    """
    
    elements = git_version.split('.')
    eups_version = 'v'+'_'.join(elements)
    return(eups_version)

def eups2git_ref(eups_ref,
                 repo,
                 versiondb = 'https://raw.githubusercontent.com/lsst/versiondb/master/ver_db'):
    
    """
    Given an eups tag (master-g3b482c0804 or v10_0) give back the git ref (3b482c0804)
    """

    # Thought of trying to parse the eups tag for the ref, but given
    # that doesn't help with the tag-based versions, might as well
    # look up versiondb for everything

    # eg. https://github.com/lsst/versiondb/blob/master/ver_db/afw.txt
    shafile = versiondb + '/' + repo + '.txt'

    # split the eups_ref into version+N, add a 0 if none
    if '+' in eups_ref:
        version, goaround = eups_ref.rsplit('+', 2)
    else:
        # make sure this is a string, or comparison trouble later
        version, goaround = (eups_ref, '0')

    # Get the file tying shas to eups versions
    http = urllib3.PoolManager()
    refs = http.request('GET', shafile)
    if refs.status >= 300: raise RuntimeError("Failed GET with HTTP code",refs.status)
    reflines = refs.data.split('\n')

    found = False
    for refline in reflines:
        # skip the ones not even keyed on the right version
        if not refline.startswith(version): continue
        eupsver, sha, rebuild = refline.split()
        # skip for the wrong rebuild
        if rebuild != goaround: continue
        # get out if we find it
        if rebuild == goaround:
            found = True
            break

    # oops if we didn't find it
    if not found: raise RuntimeError('Whoah! did not find', version, goaround, repo)

    return(sha)

            



        
        


    

    
    

