#!/bin/sh
# The shared exit. Both controls are bound here, so neither is optional.
set -eu
python3 -c 'import sys; sys.path.insert(0, "src"); import indexer, pinned_tool; indexer.materialize_index(sys.argv[1:]); sys.exit(pinned_tool.pinned_tool(sys.argv[1:]))' "$@"
