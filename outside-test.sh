#!/bin/bash

if (( $# != 1 )); then
  echo "Which repo shall I test?"
  exit 1
fi
REPO="https://github.com/ukc-co663/dependency-solver-$1"
chmod -R +w temp-playground
rm -rf temp-playground
cp -r tests temp-playground
chmod -R -w temp-playground
docker run -v $PWD/temp-playground:/depsolver/tests rgrig/ukc-co663-depsolver tests/inside-test.sh $REPO
