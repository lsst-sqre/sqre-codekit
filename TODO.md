# TODO

## codekit

### `github-tag-release`

- use manifest ID from eups tag file, if present, making `--manifest` optional

- (MAYBE) remove auto-magical eups -> git tag managling from
  `github-tag-release`?

- (MAYBE) check for `v`/non-`v` prefixed version of tag to ensure that a repo
  does not have both `vX.X.X` and `X.X.X` release tags?

- (MAYBE) insert eups product version string into git tag message?

### `github-tag-teams`

- (MAYBE) add list of refs to `github-tag-teams` to try before falling back to
  tagging the github default branch. This would allow branches to be created
  before release tags are created.

### `github-fork-org`

- Support forking of addition repos into destination org when member teams
  already exist.

### general

- check github ratelimit prior to starting operations and bail out if the
  remaining call limit is low

- move guts of console scripts into modules so they can be unit tested

- README

    - review technical debt comments in console scripts

    - example of creating/tearing down test org w/ blurb on github manual org
     creation

    - debug levels

    - `<service>-<verb>-<noun>` naming pattern???

    - mention `github.GithubException.RateLimitExceededException`

- automated acceptance tests -- possible use live github by initializing an
  org(s) as needed for the test?
