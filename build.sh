#!/bin/sh
# Build James Pond 2: Codename Robocod from your own copy of the game:
#     ./build.sh DISC.hfe          (the disc, as an HxC .hfe: its copy
#                                   protection reads it sector by sector)
# then: cd recomp && ./robocod
# The steps are recipe.json's "build", run by SuperSpider's tools/weave.py.
set -e
HERE="$(cd "$(dirname "$0")" && pwd)"
SUPERSPIDER="${SUPERSPIDER:-$HOME/stuff/superspider}"
[ $# -gt 0 ] || { echo "usage: $0 DISC.hfe" >&2; exit 2; }
(cd "$SUPERSPIDER" && dune build)
WEAVE_RECIPES="$HERE" exec python3 -I "$SUPERSPIDER/tools/weave.py" build "$@"
