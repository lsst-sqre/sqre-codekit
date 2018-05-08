"""
pygithub based functions intended to replace the github3.py based functions in
codetools.
"""

import logging
import github
import codekit.codetools as codetools
from public import public
from github import Github

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


@public
def find_tag_by_name(repo, tag_name):
    """Find tag by name in a github Repository

    Parameters
    ----------
    repo: :class:`github.Repository` instance

    tag_name: str
        Short name of tag (not a fully qualified ref).

    Returns
    -------
    gh : :class:`github.GitRef` instance or `None`
    """
    tagfmt = 'tags/{ref}'.format(ref=tag_name)

    try:
        ref = repo.get_git_ref(tagfmt)
        if ref and ref.ref:
            return ref
    except github.UnknownObjectException:
        pass

    return None
