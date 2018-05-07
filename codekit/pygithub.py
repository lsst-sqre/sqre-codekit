"""
pygithub based functions intended to replace the github3.py based functions in
codetools.
"""

import logging
from public import public
from github import Github
import codekit.codetools as codetools

logging.basicConfig()
logger = logging.getLogger('codekit')


@public
def login_github(token_path=None, token=None):
    """Log into GitHub using an existing token.

    Parameters
    ----------
    token_path : str, optional
        Path to the token file. The default token is used otherwise.

    token: str, optional
        Literial token string. If specifified, this value is used instead of
        reading from the token_path file.

    Returns
    -------
    gh : :class:`github.GitHub` instance
        A GitHub login instance.
    """

    token = codetools.github_token(token_path=token_path, token=token)
    return Github(token)
