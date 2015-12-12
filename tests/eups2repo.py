from __future__ import print_function
import sys
import unittest
import codekit.codetools as codetools

class Eups2RepoTest(unittest.TestCase):

    def testrepocheck(self):
        repo = codetools.eups2repo('lsst_apps')
        print(repo, file=sys.stderr)
        self.assertEqual(repo,'lsst_apps')

