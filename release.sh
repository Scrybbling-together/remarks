#!/bin/bash

# Exit if the working tree is dirty
if [ -n "$(git status --porcelain)" ]; then
    echo "Error: Working tree is dirty. Please commit or stash your changes."
    exit 1
fi

# Exit if the current branch is not "main"
CURRENT_BRANCH=$(git rev-parse --abbrev-ref HEAD)
if [ "$CURRENT_BRANCH" != "main" ]; then
    echo "Error: Current branch is not 'main'. Please switch to the main branch."
    exit 1
fi

COMMIT=$(git rev-parse main)
echo "Building latest version of the remarks-server based on the main branch"
nix build .#dockerServer
LINE_OUT=$(docker load < result)
CONTAINER_TAG=$(echo "$LINE_OUT" | awk '{ print $3 }')
echo "Built the container remarks-server:$COMMIT"
docker tag "$CONTAINER_TAG" remarks-server:"$COMMIT"
docker tag "$CONTAINER_TAG" remarks-server:latest
echo "Pushing!"
docker push remarks-server:"$COMMIT"
docker push remarks-server:latest
