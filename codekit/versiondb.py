"""versionDB related utility functions."""

from codekit.codetools import debug
from public import public
import logging
import re
import requests
import textwrap

default_base_url =\
    'https://raw.githubusercontent.com/lsst/versiondb/master/manifests'


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


# ~duplicates the Manifest class in lsst_buid/python/lsst/ci/prepare.py but
# operates over http rather than on a local git clone
class Manifest(object):
    """Representation of a "versionDB" manifest. AKA `bNNNN`. AKA `bxxxx`. AKA
    `BUILD`. AKA `BUILD_ID`. AKA `manifest`.

    Parameters
    ----------
    name: str
        Name of the manifest . Eg., `b1234`

    base_url: str
        Base url to the path for `manifest` files`. Optional.

        Eg.:
            `https://raw.githubusercontent.com/lsst/versiondb/master/manifests`
    """

    def __init__(self, name, base_url=None):
        self.name = name
        self.base_url = default_base_url
        if base_url:
            self.base_url = base_url

    def __fetch_manifest_file(self):
        # construct url
        tag_url = '/'.join((self.base_url, self.name + '.txt'))
        debug("fetching: {url}".format(url=tag_url))

        r = requests.get(tag_url)
        r.raise_for_status()

        self.__text = r.text

    def __parse_manifest_text(self):
        products = {}

        for n, line in enumerate(self.__text.splitlines(), start=1):
            if not isinstance(line, str):
                line = str(line, 'utf-8')

            # skip commented out and blank lines
            if line.startswith('#') or line == '':
                continue
            if line.startswith('BUILD'):
                pat = r'^BUILD=(b\d{4})$'
                m = re.match(pat, line)
                if not m:
                    raise RuntimeError(textwrap.dedent("""
                        Unparsable versiondb manifest:
                          {line}
                        """).format(
                        line=line,
                    ))
                parsed_name = m.group(1)
                continue

            try:
                # min of 3, max of 4 fields
                fields = line.split()[0:4]
                (name, sha, eups_version) = fields[0:3]
            except ValueError as e:
                raise ValueError(
                    "error parsing manifest {name} at line {n}:\n{e}".format(
                        name=self.name,
                        n=n,
                        e=e,
                    )) from None

            products[name] = {
                'name': name,
                'sha': sha,
                'eups_version': eups_version,
                'dependencies': [],
            }

            # the 4th field, if present, is a csv list of deps
            if len(fields) == 4:
                dependencies = fields[3:4][0].split(',')
                products[name]['dependencies'] = dependencies

        # sanity check tag name in the file
        if not self.name == parsed_name:
            raise RuntimeError(textwrap.dedent("""
                name in data              : ({dname})
                  does not match file name: ({fname})\
                """).format(
                dname=parsed_name,
                fname=self.name,
            ))

        self.__products = products

    def __process(self):
        self.__fetch_manifest_file()
        self.__parse_manifest_text()

    @property
    def products(self):
        """Return Dict of products described by the manifest"""
        # check for cached data
        try:
            return self.__products
        except AttributeError:
            pass

        self.__process()

        return self.__products
