#!/bin/bash

LOG="release.log"
echo "" > $LOG

#if [ -n "$(git status --porcelain)" ]; then
#    echo "Error: Working tree is dirty. Please commit or stash your changes."
#    exit 1
#fi

CURRENT_BRANCH=$(git rev-parse --abbrev-ref HEAD)
if [ "$CURRENT_BRANCH" != "main" ]; then
    echo "Error: Current branch is not 'main'. Please switch to the main branch."
    exit 1
fi

gum format -- "# Building and releasing **the remarks-server docker container**"

gum spin --spinner dot --title "Building container" --show-output -- nix build .#dockerServer &>> $LOG

SOURCE_IMAGE=$(docker load < result | awk '{ print $3}')
COMMIT=$(git rev-parse main)

gum spin --spinner dot --title "Loading container into docker" --show-output -- docker load < result
echo "$GUM_SPIN_SHOW_OUTPUT" >> $LOG

COMMIT_TAG="laauurraaa/remarks-server:$COMMIT"
LATEST_TAG="laauurraaa/remarks-server:latest"
gum format <<EOF
## Built tags

**$COMMIT_TAG**
**$LATEST_TAG**
EOF

docker tag "$SOURCE_IMAGE" "$COMMIT_TAG" &>> $LOG
docker tag "$SOURCE_IMAGE" "$LATEST_TAG" &>> $LOG

gum format -- "## Pushing to docker hub!"

gum spin --spinner dot --title "Pushing commit tag to docker hub" --show-output -- docker push -q "$COMMIT_TAG"
PUSH_COMMIT_EXIT_CODE=$?
echo "$GUM_SPIN_SHOW_OUTPUT" >> $LOG
gum spin --spinner dot --title "Pushing latest tag to docker hub" --show-output -- docker push -q "$LATEST_TAG"
PUSH_LATEST_EXIT_CODE=$?
echo "$GUM_SPIN_SHOW_OUTPUT" >> $LOG

if [ $PUSH_COMMIT_EXIT_CODE -eq 0 ]; then
  gum format <<EOF
Commit tag container **successfully pushed**: \`$COMMIT_TAG\`
EOF
else
  gum format <<EOF
Commit tag container **failed to push**
EOF
fi
if [ $PUSH_LATEST_EXIT_CODE -eq 0 ]; then
  gum format <<EOF
Latest tag container **successfully pushed**: \`$LATEST_TAG\`
EOF
else
  gum format <<EOF
Latest tag container **failed to push**
EOF
fi


