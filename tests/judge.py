#!/usr/bin/env python3

from argparse import ArgumentParser
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
  sys.stderr.write('E: {}\n'.format(m))
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
    if not re.match('[a-zA-Z]+=[.0-9]+', reference):
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
    m = re.match('([a-zA-Z])((=|<|>|<=|>=)([.0-9]+))?', rangestr)
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
    if self.minimum:
      r += '>'
    if self.maximum:
      r += '<'
    if self.inclusive:
      r += '='
    if self.minimum:
      r += str(self.minimum)
    if self.maximum:
      r += str(self.maximum)
    return r

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

  def satisfiedBy(self, package):
    inRange = self.packageRange.has(package)
    if self.kind == '+':
      return inRange
    else:
      return not inRange

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


def satisfies(constraint):
  for p in state:
    if constraint.satisfiedBy(p):
      return True
  return False

def valid():
  for p in state:
    if p not in repository:
      return False
  for p in state:
    for clause in repository[p].depends:
      if not any(satisfies(Constraint('+{}'.format(qr))) for qr in clause):
        return False
  for p in state:
    if any(satisfies(Constraint('+{}'.format(qr))) for qr in repository[p].conflicts):
      return False
  return True

def main():
  global commands
  global final_constraints
  global state
  global repository
  args = argparser.parse_args()
  load_all(args)
  if not valid():
    error('initial state is invalid')
  cost = 0
  for c in commands:
    if c.action == '+':
      if c.package in state:
        error('package already installed: {}'.format(c.package))
      if c.package not in repository:
        error('package not in repository: {}'.format(c.package))
      state.add(c.package)
      cost += repository[c.package].size
    else:
      if c.package not in state:
        error('package not installed: {}'.format(c.package))
      state.remove(c.package)
      cost += 1
    if not valid():
      error('command leads to invalid state: {}'.format(c))
  for c in final_constraints:
    if not satisfies(c):
      error('constraint not satisfied: {}'.format(c))
  sys.stdout.write('cost {}\n'.format(cost))

if __name__ == '__main__':
  main()
