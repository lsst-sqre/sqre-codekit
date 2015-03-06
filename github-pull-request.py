#!/usr/bin/env python

import os
import getpass
import argparse

def main(issue, user, branch, repo, base="master"):
    pwd = getpass.getpass()
    cmd = 'curl --user "%s:%s"' % (user, pwd)
    del pwd
    cmd += " --request POST"
    cmd += """ --data '{"issue": "%d", "head": "%s:%s", "base": "%s"}'""" % (issue, user, branch, base)
    cmd += " https://api.github.com/repos/%s/pulls" % repo
    os.system(cmd)

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("issue", type=int, help="Issue number")
    parser.add_argument("user", help="Your user name")
    parser.add_argument("branch", help="Pull from this branch in your repo")
    parser.add_argument("repo", help="Repository name to receive pull request")
    parser.add_argument("--base", default="master", help="Branch to pull into")
    args = parser.parse_args()
    main(args.issue, args.user, args.branch, args.repo, base=args.base)
