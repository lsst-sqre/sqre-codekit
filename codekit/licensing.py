"""Utilities for maintaining and asserting LICENSE and COPYRIGHT in
LSST DM repos.
"""

import os
import fnmatch
import re
import time

import requests
import git


comment_pattern = re.compile(
    '(?P<comment_flag>^[#* ]*)(?P<content>[\d\w\s<]*)')


def convert_boilerplate(code_stream):
    """Convert old-style licensing boilerplate (with full GPLv3) to RFC-45
    style.

    Parameters
    ----------
    code_stream : file-like object
        File handle to code.

    Returns
    -------
    converted_text : str
        Converted code text, as a string.
    """
    # Text for the new copyright/license boilerplate
    template_lines = [
        '{comment} See the COPYRIGHT and LICENSE files in the top-level '
        'directory of this\n',
        '{comment} package for notices and licensing terms.\n'
    ]
    lines = code_stream.readlines()
    new_lines = []
    omitting_mode = False
    for line in lines:
        m = comment_pattern.match(line)
        if m is None:
            # Pass through of non-comment characters
            new_lines.append(line)
            continue

        content = m.group('content').lstrip()
        if m is not None and content.startswith('Copyright'):
            # Trigger replacement at start of Copyright block
            # Make it the template's responsibility to add a single space
            # after the comment prefix string
            comment_text = m.group('comment_flag').rstrip()
            for template_line in template_lines:
                new_lines.append(
                    template_line.format(comment=comment_text))
            omitting_mode = True
        elif content.startswith('see <http'):
            # End replacement mode
            omitting_mode = False
        elif omitting_mode is False:
            # Pass through mode
            if line.rstrip() == '#':
                # remove whitespace from comment header/footer for Python
                new_lines.append('#\n')
            else:
                new_lines.append(line)
    return ''.join(new_lines)


def list_development_years(repo):
    """List the years when a repo was actively developed.

    This function does not search all branches; only the history of `repo`'s
    currently active branch.

    Parameters
    ----------
    repo : :class:`git.Repo` instance
        The GitPython repo instance for this repository.

    Returns
    -------
    years : tuple
        The years where a commit occured in this repo's git history.
    """
    years = []
    for commit in repo.iter_commits():
        struct_time = time.gmtime(commit.authored_date)
        years.append(struct_time.tm_year)
    years = list(set(years))
    years.sort()
    return tuple(years)


def write_lsst_license(path, url=None):
    """Write the LSST license into `path`.

    The license is read from a url, which is at
    http://www.lsstcorp.org/LegalNotices/GPLv3License.txt
    by default. However, the source `url` can be modified.

    Parameters
    ----------
    path : str
        Path to write license file into.
    url : str, optional
        URL to find the source license at. Defaults to the lsstcorp.org license
        file by default.
    """
    if url is None:
        url = 'http://www.lsstcorp.org/LegalNotices/GPLv3License.txt'
    license = requests.get(url)
    with open(path, 'w') as f:
        f.write(license.text)


def write_default_copyright(path, repo):
    """Write a default COPYRIGHT file according to RFC-45.

    The default copyright is assigned to LSST/AURA. The years are machine-
    supplied from git history.

    We expect authors from other institutions to add their own copyright lines.
    We also expect that the years in this COPYRIGHT file will be
    maintained with a bot.

    Parameters
    ----------
    path : str
        Path to write the copyright file onto.
    repo : :class:`git.Repo` instance
        The GitPython repo instance for this repository.
    """
    template = 'Copyright {y} The LSST DM Developers\n'
    dev_years = list_development_years(repo)
    if len(dev_years) == 1:
        year_str = str(dev_years[0])
    else:
        year_str = '{0}-{1}'.format(min(dev_years), max(dev_years))
    with open(path, 'w') as f:
        f.write(template.format(y=year_str))


def upgrade_repo(gh, github_repo, branch_name, clone_dir):
    """Process a repository and upgrade licensing/copyright to RFC-45 style.

    *Note*: the repository is cloned into `clone_dir`, and changes are
    pushed back to the remote on the `branch_name` branch. However, the
    local clone is not cleaned up. Use :class:`codekit.TempDir` to create
    a self-cleaning temporary directory for the clone.

    Parameters
    ----------
    gh : obj
        A GitHub session, usually created by
        :func:`codekit.codetools.login_github`.
    github_repo : obj
        A GitHub repo, generated by `github3`.
    branch_name : str
        Name of the branch to create from master and commit in.
    clone_dir : str
        Directory to clone the repository into.
    """
    # Clone repo
    repo = git.Repo.clone_from(github_repo.clone_url, clone_dir)

    # Create a ticket branch to work in
    ticket_branch = repo.create_head(branch_name)
    ticket_branch.checkout()

    # Covert boilerplate
    patterns = ('*.py', '*.cpp', '*.cc', '*.h')
    for filepath in all_files(clone_dir, patterns=patterns):
        with open(filepath, 'r') as f:
            new_code = convert_boilerplate(f)
        with open(filepath, 'w') as f:
            f.write(new_code)
        repo.index.add([filepath])
    if repo.is_dirty():
        repo.index.commit('Upgrade license and copyright according to RFC-45')

    # Add LSST license file
    license_path = os.path.join(clone_dir, 'LICENSE')
    write_lsst_license(license_path)
    repo.index.add([license_path])
    repo.index.commit('Add LICENSE file according to RFC-45')

    # Add default COPYRIGHT file, sensitive to git timelines
    copyright_path = os.path.join(clone_dir, 'COPYRIGHT')
    write_default_copyright(copyright_path, repo)
    repo.index.add([copyright_path])
    repo.index.commit('Add COPYRIGHT file according to RFC-45')

    # push branch to remote
    assert repo.is_dirty() is False
    remote = repo.remote(name='origin')
    refspec = 'refs/heads/{br}:refs/heads/{br}'.format(br=branch_name)
    remote.push(refspec=refspec)


def all_files(root, patterns=('*',)):
    # Expand patterns from semicolon-separated string to list
    """Iterate through files matching a pattern.

    Adapted from Receipe 2.16 of the Python Cookbook, 2nd Ed [1].

    Parameters
    ----------
    root : str
        Root directory to process files in.
    patterns : tuple
        An iterable of strings for searching filenames.
        e.g. ``('*.py*, '*.cpp')``.

    Yields
    ------
    path : str
        Path to a file matching the `patterns`.

    References
    ----------
    .. [1] Martelli, A., Ravenscroft, A., & Ascher, D. (2005). *Python
       Cookbook.* O'Reilly Media, Inc..
    """
    for path, subdirs, files in os.walk(root):
        files.sort()
        for name in files:
            for pattern in patterns:
                if fnmatch.fnmatch(name, pattern):
                    yield os.path.join(path, name)
                    break
