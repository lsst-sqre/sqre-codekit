#!/usr/bin/env python

import os
import getpass
import argparse


def parse_args():
    parser = argparse.ArgumentParser(
        prog='github-pull-request')
    parser.add_argument("issue", type=int, help="Issue number")
    parser.add_argument("user", help="Your user name")
    parser.add_argument("branch", help="Pull from this branch in your repo")
    parser.add_argument("repo", help="Repository name to receive pull request")
    parser.add_argument("--base", default="master", help="Branch to pull into")
    return parser.parse_args()


def main():
    args = parse_args()
    pwd = getpass.getpass()

    cmd = 'curl --user "%s:%s"' % (args.user, pwd)
    del pwd
    cmd += " --request POST"
    cmd += """ --data '{"issue": "%d", "head": "%s:%s", "base": "%s"}'""" % (args.issue, args.user, args.branch, args.base)  # NOQA
    cmd += " https://api.github.com/repos/%s/pulls" % args.repo
    os.system(cmd)


if __name__ == "__main__":
    main()
