#!/bin/bash

for repo in $(cat repos.txt); do
  echo "REPO $repo"
  ./outside-test.sh $repo | tee scoreboard/$repo.log.txt
done
