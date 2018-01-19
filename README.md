Homework: Dependency Solver
===========================

Continue reading here only after you read the problem description you were
given in lectures.


Grading
-------

You will be graded automatically using the following process. If this automatic
process fails, you will get 0 marks. It is your responsibility to ensure the
commands listed below work.

1.  On a clean and updated Ubuntu 16.04, your repository is cloned, and your
code is built, using the following commands:

```
git clone YOUR_REPO depsolver
cd depsolver
make all
```

2. Each test consists of three files (REPOSITORY, INITIAL, and CONSTRAINTS), as
described in the problem statement. Your solver is run on each test, and its
output scored using these commands:

```
( ulimit -t 300 -v 1000000 ; ./solve REPOSITORY INITIAL CONSTRAINTS > COMMANDS )
judge.py REPOSITORY INITIAL COMMANDS CONSTRAINTS
```

The limit on time and memory is necessary for pragmatic reasons: we cannot
wait forever to see if a program eventually produces an answer, and the server
has a limited amount of memory. If 5min of runtime and 1GB of memory is not
enough for your program, then it probably has a serious problem with efficiency
anyway. Fix it.

You can find the judge script in `tests/judge.py`. If you notice a problem with
the script, file an issue. If you find a way to improve the script, send a
Pull Request.

3. If the judge issues an error, you receive 0 points for that test. Otherwise,
you receive 1 point for correctness. If the test is one of the known tests
(i.e., one of those you have been given), then you also receive minC/C points
for efficiency, where C is the cost of your solution and minC is the smallest
known cost for the test. The smallest known cost will be made public, but might
decrease as others (peers and instructors) find better solutions. (We guarantee
that minC is positive.)

