#!/bin/bash

if (( $# < 1 )); then
  echo "Which git repo shall I test?"
  exit 1
fi

git clone $1 to-test
cd to-test
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
  echo "TEST $T"
  TD=$D/$T
  ( ulimit -t 300 -m 1000000 ; ./solve $TD/repository.json $TD/initial.json $TD/constraints.json > commands.json 2> stderr ) && \
  $D/judge.py $TD/repository.json $TD/initial.json commands.json $TD/constraints.json
done
