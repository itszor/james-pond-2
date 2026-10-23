#!/bin/sh
# Build James Pond from your own copy of the game:
#     ./build.sh "James Pond (1990)(Krisalis).adf"      (or the [a] dump, the TOSEC zip,
#                                                       or the Buzz re-release's .hfe)
# then: cd recomp && ./jamespond
# The steps are recipe.json's "build", run by SuperSpider's tools/weave.py.
set -e
HERE="$(cd "$(dirname "$0")" && pwd)"
SUPERSPIDER="${SUPERSPIDER:-$HOME/stuff/superspider}"
[ $# -gt 0 ] || { echo "usage: $0 DISC.adf | GAME.zip | DISC.hfe" >&2; exit 2; }
(cd "$SUPERSPIDER" && dune build)
WEAVE_RECIPES="$HERE" exec python3 -I "$SUPERSPIDER/tools/weave.py" build "$@"
