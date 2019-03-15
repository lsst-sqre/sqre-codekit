"""EUPS distrib tag related utility functions."""

from codekit.codetools import debug
from public import public
import logging
import re
import requests
import textwrap

default_pkgroot = 'https://eups.lsst.codes/stack/src'


@public
def setup_logging(verbosity=0):
    # enable requests debugging
    # based on http://docs.python-requests.org/en/latest/api/?highlight=debug
    if verbosity and verbosity > 1:
        from http.client import HTTPConnection
        HTTPConnection.debuglevel = 1

        requests_log = logging.getLogger("urllib3")
        requests_log.setLevel(logging.DEBUG)
        requests_log.propagate = True


class EupsTag(object):
    """Representation of an eups distrib tag (`<name>.list`) file.

    Parameters
    ----------
    name: str
        Name of the tag. Eg., `w_2018_18` or `v15_0`

    base_url: str
        Base url to the path for `tags` under an `EUPS_PKGROOT`. Optional.

        Eg., `https://eups.lsst.codes/stack/src/tags`
    """

    def __init__(self, name, base_url=None):
        self.name = name
        # note that we are not parsing `config.txt` from the pkgroot and are
        # assuming tags live under `./tags/`
        self.base_url = '/'.join((default_pkgroot, 'tags'))
        if base_url:
            self.base_url = base_url

    def __fetch_tag_file(self):
        # construct url
        tag_url = '/'.join((self.base_url, self.name + '.list'))
        debug("fetching: {url}".format(url=tag_url))

        r = requests.get(tag_url)
        r.raise_for_status()

        self.__text = r.text

    def __parse_tag_text(self):
        products = {}

        parsed_name = None
        for n, line in enumerate(self.__text.splitlines(), start=1):
            if not isinstance(line, str):
                line = str(line, 'utf-8')

            if line.startswith('EUPS'):
                pat = r'^EUPS distribution ([^ ]+) version list. Version 1.0$'
                m = re.match(pat, line)
                if not m:
                    raise RuntimeError(textwrap.dedent("""
                        Unknown line format:
                          {line}
                        """).format(
                        line=line,
                    ))
                parsed_name = m.group(1)
                continue
            # versiondb ref, present in d_2018_05_08 and later
            if line.startswith('#BUILD'):
                pat = r'^#BUILD=(b\d{4})$'
                m = re.match(pat, line)
                if not m:
                    raise RuntimeError(textwrap.dedent("""
                        Unparsable versiondb manifest:
                          {line}
                        """).format(
                        line=line,
                    ))
                manifest = m.group(1)
                continue
            # skip commented out and blank lines
            if line.startswith('#') or line == '':
                continue

            try:
                # extract the repo and eups tag
                (name, flavor, eups_version) = line.split()[0:3]
            except ValueError as e:
                raise ValueError(
                    "error parsing eups tag {name} at line {n}:\n{e}".format(
                        name=self.name,
                        n=n,
                        e=e,
                    ))

            products[name] = {
                'name': name,
                'flavor': flavor,
                'eups_version': eups_version,
            }

        # sanity check tag name in the file
        if not self.name == parsed_name:
            raise RuntimeError(textwrap.dedent("""
                name in data              : ({dname})
                  does not match file name: ({fname})\
                """).format(
                dname=parsed_name,
                fname=self.name,
            ))

        try:
            self.__manifest = manifest
        except NameError:
            self.__manifest = None
        self.__products = products

    def __process(self):
        self.__fetch_tag_file()
        self.__parse_tag_text()

    @property
    def products(self):
        """Return List of products described by the tag"""
        # check for cached data
        try:
            return self.__products
        except AttributeError:
            pass

        self.__process()

        return self.__products

    @property
    def manifest(self):
        """Return versionDB manifest ID, if present in the eups tag file"""
        # check for cached data
        try:
            return self.__manifest
        except AttributeError:
            pass

        self.__process()

        return self.__manifest


@public
def git_tag2eups_tag(git_tag):
    """Convert git tag to an acceptable eups tag format

    I.e., eups no likey semantic versioning markup, wants underscores

    Parameters
    ----------
    git_tag: str
        literal git tag string

    Returns
    -------
    eups_tag: string
        A string suitable for use as an eups tag name
    """
    eups_tag = git_tag

    # eups tags should not start with a numeric value -- prefix `v` if
    # it does
    if re.match(r'\d', eups_tag):
        eups_tag = "v{eups_tag}".format(eups_tag=eups_tag)

    # convert '.'s and '-'s to '_'s
    eups_tag = eups_tag.translate(str.maketrans('.-', '__'))

    return eups_tag
