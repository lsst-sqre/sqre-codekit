[![Build Status](https://travis-ci.org/lsst-sqre/sqre-codekit.svg?branch=master)](https://travis-ci.org/lsst-sqre/sqre-codekit)

# sqre-codekit

LSST DM SQuaRE misc. code management tools

## Installation

sqre-codekit runs on Python 3.6 or newer. You can install it with

```bash
pip install sqre-codekit
```

## Available commands

- `github-auth`: Generate a GitHub authentication token.
- `github-decimate-org`: Delete repos and/or teams from a GitHub organization.
- `github-fork-org`: Fork repositories from one GitHub organization to another.
- `github-get-ratelimit`: Display the current github ReST API request ratelimit.
- `github-list-repos`: List repositories on Github using various criteria.
- `github-mv-repos-to-team`: Move repo(s) from one team to another.
- `github-tag-release`: Tag git repositories, in a GitHub org, that correspond
    to the products in a published eups distrib tag.
- `github-tag-teams`: Tag the head of the default branch of all repositories in
    a GitHub org which belong to the specified team(s).

Use the `--help` flag with any command to learn more.

## Example usage

### `github-auth`

To generate a personal user token (you will be prompted for your password):

```bash
github-auth -u {{username}}
```

Or to generate a token with delete privileges:

```bash
github-auth -u {{username}} --delete-role
```

### `github-fork-org`

To clone all [github.com/lsst](https://github.com/lsst) repos into an GitHub
organization called `{{username}}-shadow`:

```bash
github-fork-org \
    --dry-run \
    --debug \
    --src-org 'lsst' \
    --dst-org '{{username}}-shadow' \
    --token "$GITHUB_TOKEN" \
    --team 'DM Auxilliaries' \
    --team 'DM Externals' \
    --team 'Data Management' \
    --copy-teams

```

You'll need to create this shadow organization in advance. Working in a shadow
organization is useful for testing.

### `github-decimate-org`

If you want to take a recent fork, you will need to delete the existing shadow
repos first:

```bash
github-decimate-org \
    --dry-run \
    --debug \
    --org 'example' \
    --token "$GITHUB_TOKEN" \
    --delete-repos \
    --delete-repos-limit 3 \
    --delete-teams \
    --delete-teams-limit 3
```

That requires a token with delete privileges.

To get more debugging information, set your `DM_SQUARE_DEBUG` variable before
running any command, or use the `-d` debug flag on the command line.

### `github-tag-release`

XXX

### `github-tag-teams`

XXX

### `github-get-ratelimit`

XXX

## Development

To develop codekit, create a Python virtual environment, and

```bash
git clone https://github.com/lsst-sqre/sqre-codekit.git
cd sqre-codekit
virtualenv venv
. venv/bin/activate
pip install -r requirements.txt
python setup.py develop
```

Note that all scripts (in `codekit/cli`) are installed using setuptools
`entry_points`. See `setup.py`.

### tests

Unit tests can be run with [pytest](http://pytest.org/latest/):

```bash
python setup.py test
```

or

```bash
pytest tests
```
