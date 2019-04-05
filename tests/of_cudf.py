#!/usr/bin/env python3

from argparse import ArgumentParser
from collections import defaultdict
from pathlib import Path
from random import randrange
from judge import Constraint, error, Package, PackageProperties, PackageRange

import bz2
import gzip
import json
import sys

argparser = ArgumentParser(description='''\
  Converts a CUDF problem into the homework format.
''')
argparser.add_argument('cudf')
argparser.add_argument('outdir', help='gets overwritten')

def parse_depends(phi_s):
  phi = []
  for c_s in phi_s.split(','):
    clause = []
    for l_s in c_s.strip().split('|'):
      clause.append(PackageRange(l_s.replace(' ', '')))
    phi.append(clause)
  return phi

def parse_conflicts(term_s):
  term = []
  for l_s in term_s.split(','):
    term.append(PackageRange(l_s.replace(' ', '')))
  return term

def parse_provides(s):
  return [x.strip() for x in s.split(',')]

# TODO: Repeatedly uninstall packages whose constraints are not satisfied.
def cleanup(all_packages, installed):
  return installed


def main():
  args = argparser.parse_args()
  all_packages = {}
  initial_state = set()
  constraints = []
  open_cudf = open
  if args.cudf.endswith('.bz2'):
    open_cudf = bz2.open
  elif args.cudf.endswith('.gz'):
    open_cudf = gzip.open
  with open_cudf(args.cudf, 'rt') as cudf_file:
    installed_version = defaultdict(int)
    package_name = None
    package_version = None
    package_size = None
    package_installed = False
    package_depends = []
    package_conflicts = []
    package_provides = []
    def record_package():
      nonlocal package_name
      nonlocal package_version
      nonlocal package_size
      nonlocal package_installed
      nonlocal package_depends
      nonlocal package_conflicts
      nonlocal package_provides
      nonlocal all_packages
      nonlocal initial_state
      if package_name is None:
        return
      if package_version is None:
        error('package without version: {}'.format(package_name))
      if package_size is None:
        package_size = 100 + randrange(1000000)
        #error('package without size: {}={}'.format(package_name, package_version))
      name_version = '{}={}'.format(package_name, package_version)
      package = Package(name_version)
      new_conflicts = []
      package_provides = set(package_provides)
      for r in package_conflicts:
        if r.name in package_provides:
          continue # FIXME: should conflict with other providers (check cudf spec!)
        if r.has(package):
          # TODO: try also adding >
          r = PackageRange('{}<{}'.format(package.name, package.version))
        new_conflicts.append(r)
      props = PackageProperties(package_depends, new_conflicts, package_size)
      if package in all_packages:
        error('repeated package: {}'.format(package))
      all_packages[package] = props
      if package_installed:
        initial_state.add(package)
        installed_version[package.name] = int(package_version)
      for p in package_provides:
        provided = Package('{}=0'.format(p))
        if provided not in all_packages:
          provided_props = PackageProperties([[]], [], 0)
          all_packages[provided] = provided_props
        if package_installed:
          initial_state.add(provided)
        all_packages[provided].depends[0].append(PackageRange(name_version))
      package_name = None
      package_version = None
      package_size = None
      package_installed = False
      package_depends = []
      package_conflicts = []
      package_provides = []
    def record_upgrade(s):
      names = [x.strip() for x in s.split(',')]
      for n in names:
        constraints.append(Constraint('+{}>={}'.format(n,installed_version[n])))
    def record_install(s):
      packages = [x.replace(' ', '') for x in s.split(',')]
      for p in packages:
        constraints.append(Constraint('+{}'.format(p)))
    for line in cudf_file:
      if line.startswith('package'):
        record_package()
        package_name = line.split()[1]
      elif line.startswith('version'):
        package_version = line.split()[1]
      elif line.startswith('size'):
        package_size = int(line.split()[1])
      elif line.startswith('installed:'):
        package_installed = bool(line.split()[1])
      elif line.startswith('depends:'):
        package_depends = parse_depends(line[len('depends:'):].strip())
      elif line.startswith('conflicts:'):
        package_conflicts = parse_conflicts(line[len('conflicts:'):].strip())
      elif line.startswith('provides:'):
        package_provides = parse_provides(line[len('provides:'):].strip())
      elif line.startswith('upgrade:'):
        record_upgrade(line[len('upgrade:'):].strip())
      elif line.startswith('install:'):
        record_install(line[len('install:'):].strip())
    record_package()
  initial_state = cleanup(all_packages, initial_state)
  outdir = Path(args.outdir)
  outdir.mkdir(parents=True, exist_ok=True)
  with (outdir/'repository.json').open(mode='w') as out:
    repository = []
    for package, props in all_packages.items():
      p = {}
      p['name'] = package.name
      p['version'] = str(package.version)
      p['size'] = props.size
      p['depends'] = [[str(l) for l in c] for c in props.depends]
      p['conflicts'] = [str(l) for l in props.conflicts]
      repository.append(p)
    json.dump(repository, out)
  with (outdir/'initial.json').open(mode='w') as out:
    json.dump([str(p) for p in initial_state], out)
  with (outdir/'constraints.json').open(mode='w') as out:
    json.dump([str(c) for c in constraints], out)

if __name__ == '__main__':
  main()
