#!/bin/sh
set -eu
git checkout "$@"
python3 -c 'import sys; sys.path.insert(0, "src"); import index; print("indexed", index.build(), "files")'
