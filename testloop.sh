#!/usr/bin/env nix-shell

pytest --no-header "$@";

while inotifywait -q -r . -e modify,create,delete,move --include ".*\.py$"; do
  clear;
  pytest --no-header "$@";
done