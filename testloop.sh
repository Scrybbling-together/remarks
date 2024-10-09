#!/usr/bin/env nix-shell

clear;
pytest --no-header "$@";

while inotifywait -q -r . -e modify,create,delete,move --include ".*\.py$"; do
  clear;
  pytest --no-header "$@";
done