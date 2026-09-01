#!/bin/sh
# The shared exit consumers traverse in this fixture tree.
set -eu
python3 -c 'import sys; sys.path.insert(0, "src"); import pinned_tool; sys.exit(pinned_tool.pinned_tool(sys.argv[1:]))' "$@"
