#!/usr/bin/env nix-shell

clear;
pytest -v --no-header "$@";

while inotifywait -q -r . -e modify,create,delete,move --include ".*\.py$"; do
  clear;
  pytest -v --no-header "$@";
done