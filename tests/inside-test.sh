#!/bin/bash

if (( $# < 1 )); then
  echo "Which git repo shall I test?"
  exit 1
fi
REPO="https://github.com/ukc-co663/dependency-solver-2019-$1"

echo "REPO $1 $2"
git clone $REPO to-test
cd to-test
if (( $# >= 2 )); then
  git checkout $2
fi
make all
if (( $? != 0 )); then
  echo "E: 'make all' failed"
  exit 2
fi
D=../tests
TESTS=""
for i in $(seq 0 9); do
  TESTS="seen-$i $TESTS"
done
for i in $(seq 0 9); do
  TESTS="unseen-$i $TESTS"
done
for T in $TESTS; do
  echo
  echo "TEST $T"
  TD=$D/$T
  $D/limit -m 4000 -c 300 -w 330 -x "./solve $TD/repository.json $TD/initial.json $TD/constraints.json" > commands.json 2> stderr
  if (( $? )); then
    echo
    echo FAIL
    cat stderr
  else
    $D/judge.py $TD/repository.json $TD/initial.json commands.json $TD/constraints.json
  fi
done
