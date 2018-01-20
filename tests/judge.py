#!/usr/bin/env python3

from argparse import ArgumentParser
from collections import defaultdict
from functools import total_ordering

import re
import json
import sys

argparser = ArgumentParser(description='''\
  Computes the cost of a solution.

  Starting from the initial state, applies commands one by one and tracks cost.
  For each state (initial, intermediate, final), it checks if it is valid
  according to repository rules. For the final state, it checks if it satisfies
  the constraints.
''')
argparser.add_argument('repository')
argparser.add_argument('initial')
argparser.add_argument('commands')
argparser.add_argument('constraints')

commands = None
final_constraints = None
state = None
repository = None

def error(m):
  sys.stdout.write('E: {}\n'.format(m))
  sys.exit(1)

@total_ordering
class Version:
  def __init__(self, verstr):
    if not re.match('[0-9]+(.[0-9]+)*', verstr):
      error('bad version format: {}'.format(verstr))
    self.nums = tuple(int(x) for x in verstr.split('.'))

  def __hash__(self):
    return hash(self.nums)

  def __eq__(self, other):
    return self.nums == other.nums

  def __lt__(self, other):
    return self.nums < other.nums

  def __repr__(self):
    return '.'.join(str(x) for x in self.nums)

class Package:
  def __init__(self, reference):
    if not re.match('[.+a-zA-Z0-9-]+=[.0-9]+', reference):
      error('bad package format: {}'.format(reference))
    [n, v] = reference.split('=')
    self.name = n
    self.version = Version(v)

  def __hash__(self):
    return 31 * hash(self.name) + hash(self.version)

  def __eq__(self, other):
    return self.name == other.name and self.version == other.version

  def __repr__(self):
    return '{}={}'.format(self.name, self.version)

class Command:
  def __init__(self, cmdstr):
    if not re.match('[+-].*', cmdstr):
      error('bad command format: {}'.format(cmdstr))
    self.action = cmdstr[0]
    self.package = Package(cmdstr[1:])

  def __repr__(self):
    return '{}{}'.format(self.action, self.package)

class PackageRange:
  def __init__(self, rangestr):
    m = re.match('([.+a-zA-Z0-9-]+)((=|<|>|<=|>=)([.0-9]+))?', rangestr)
    if not m:
      error('bad package range format: {}'.format(rangestr))
    self.name = m.group(1)
    self.minimum = None
    self.maximum = None
    self.inclusive = False
    if m.group(2):
      self.inclusive = ('=' in m.group(3))
      v = Version(m.group(4))
      if '<' in m.group(3):
        self.maximum = v
      elif '>' in m.group(3):
        self.minimum = v
      else:
        self.minimum = self.maximum = v

  def __repr__(self):
    r = self.name
    if self.minimum and not self.maximum:
      r += '>'
    if self.maximum and not self.minimum:
      r += '<'
    if self.inclusive:
      r += '='
    if self.minimum:
      r += str(self.minimum)
    elif self.maximum:
      r += str(self.maximum)
    return r

  def __hash__(self):
    h = 0
    h = 31 * h + hash(self.name)
    h = 31 * h + hash(self.minimum)
    h = 31 * h + hash(self.maximum)
    h = 31 * h + hash(self.inclusive)
    return h

  def __eq__(self, other):
    ok = True
    ok = ok and self.name == other.name
    ok = ok and self.minimum == other.minimum
    ok = ok and self.maximum == other.maximum
    ok = ok and self.inclusive == other.inclusive
    return ok

  def has(self, package):
    if self.name != package.name:
      return False
    if self.minimum:
      if self.inclusive:
        if not (self.minimum <= package.version):
          return False
      else:
        if not (self.minimum < package.version):
          return False
    if self.maximum:
      if self.inclusive:
        if not (package.version <= self.maximum):
          return False
      else:
        if not (package.version < self.maximum):
          return False
    return True

class PackageProperties:
  def __init__(self, depends, conflicts, size):
    self.depends = depends
    self.conflicts = conflicts
    self.size = size

class Constraint:
  def __init__(self, constraintstr):
    if not re.match('[-+].*', constraintstr):
      error('bad constraint format: {}'.format(constraintstr))
    self.kind = constraintstr[0]
    self.packageRange = PackageRange(constraintstr[1:])

  def satisfied(self):
    has = any(self.packageRange.has(p) for p in state)
    if self.kind == '+':
      return has
    else:
      return not has

  def __repr__(self):
    return '{}{}'.format(self.kind, self.packageRange)

def load_commands(data):
  global commands
  commands = []
  for s in data:
    commands.append(Command(s))

def load_constraints(data):
  global final_constraints
  final_constraints = set()
  for s in data:
    final_constraints.add(Constraint(s))

def load_state(data):
  global state
  state = set()
  for s in data:
    state.add(Package(s))

def load_repository(data):
  global repository
  repository = {}
  for p in data:
    package = Package('{}={}'.format(p['name'], p['version']))
    if package in repository:
      error('package repeated in repo: {}={}'.format(p['name'], p['version']))
    depends = []
    pdep = p['depends'] if 'depends' in p else []
    for clause in pdep:
      depends.append([PackageRange(r) for r in clause])
    pconf = p['conflicts'] if 'conflicts' in p else []
    conflicts = [PackageRange(r) for r in pconf]
    size = int(p['size'])
    repository[package] = PackageProperties(depends, conflicts, size)


def load_all(args):
  with open(args.commands) as f:
    load_commands(json.load(f))
  with open(args.constraints) as f:
    load_constraints(json.load(f))
  with open(args.initial) as f:
    load_state(json.load(f))
  with open(args.repository) as f:
    load_repository(json.load(f))


def valid():
  for p in state:
    if p not in repository:
      return False
  for p in state:
    for clause in repository[p].depends:
      if not any(Constraint('+{}'.format(qr)).satisfied() for qr in clause):
        return False
  for p in state:
    if any(Constraint('+{}'.format(qr)).satisfied() for qr in repository[p].conflicts):
      return False
  return True

clauses = None
occurrences = None
packages = None
rpackages = None
watches = None

class Unsat(Exception):
  def __init__(self, ps):
    self.clause = ps
  def __str__(self):
    return ' '.join(self.s(p) for p in self.clause)
  def s(self, p):
    return ('+' if p > 0 else '-') + str(packages[abs(p)])

def find_watch(ps):
  for p in ps:
    if p < 0:
      if packages[-p] not in state:
        return p
    else:
      if packages[p] in state:
        return p
  raise Unsat(ps)

def preprocess_repository():
  global repository
  global clauses
  global occurrences
  global packages
  global rpackages
  global watches

  # We'll refer to packages by positive integers.
  packages = [None] + list(repository.keys())
  rpackages = { packages[i] : i for i in range(1, len(packages)) }

  # For each PackageRange in the repo, compute which packages it matches.
  pranges = set()
  for props in repository.values():
    for clause in props.depends:
      for constraint in clause:
        pranges.add(constraint)
    for constraint in props.conflicts:
      pranges.add(constraint)
  versions = defaultdict(list)
  for package in repository.keys():
    versions[package.name].append(package.version)
  inrange = {} # lists all packages in a given range, by their indices
  for r in pranges:
    inrange[r] = []
    for v in versions[r.name]:
      p = Package('{}={}'.format(r.name, v))
      if r.has(p):
        inrange[r].append(rpackages[p])

  # Add clauses for depends and conflicts.
  clauses = []
  occurrences = defaultdict(set)
  for package, props in repository.items():
    p = rpackages[package]
    for dclause in props.depends:
      n = len(clauses)
      new_clause = [-p]
      occurrences[-p].add(n)
      for r in dclause:
        for q in inrange[r]:
          new_clause.append(q)
          occurrences[q].add(n)
      clauses.append(new_clause)
    for r in props.conflicts:
      for q in inrange[r]:
        n = len(clauses)
        new_clause = [-p, -q]
        occurrences[-p].add(n)
        occurrences[-q].add(n)
        clauses.append(new_clause)
  watches = [find_watch(c) for c in clauses]

def set_literal(p):
  for c in occurrences[-p]:
    if watches[c] == -p:
      watches[c] = find_watch(clauses[c])

def install_package(package):
  if package in state:
    error('package already installed: {}'.format(package))
  if package not in repository:
    error('package not in repository: {}'.format(package))
  state.add(package)
  set_literal(rpackages[package])

def uninstall_package(package):
  if package not in state:
    error('package not installed: {}'.format(package))
  state.remove(package)
  set_literal(-rpackages[package])


def main():
  global commands
  global final_constraints
  global state
  global repository
  args = argparser.parse_args()
  load_all(args)
  try:
    preprocess_repository()
  except Unsat as e:
    error('invalid initial state; unsat constraint {}'.format(e))
  cost = 0
  for c in commands:
    try:
      if c.action == '+':
        install_package(c.package)
        cost += repository[c.package].size
      else:
        uninstall_package(c.package)
        cost += 1000000
    except Unsat as e:
      error('bad command {}; unsat constraint {}'.format(c, e))
  for c in final_constraints:
    if not c.satisfied():
      error('constraint not satisfied: {}'.format(c))
  sys.stdout.write('cost {}\n'.format(cost))

if __name__ == '__main__':
  main()
