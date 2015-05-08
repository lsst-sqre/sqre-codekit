"""
Module for assorted codetools scripts
"""

# technical debt
# --------------
# - package
# - check explictly for github3 version
# major API breakage between
# github3.py                 - Python wrapper for the GitHub API(http://developer.github.com/v3)
#  INSTALLED: 0.9.4
#  LATEST:    1.0.0a1

from github3 import login
import os

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
