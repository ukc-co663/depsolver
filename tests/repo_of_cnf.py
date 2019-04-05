#!/usr/bin/env python3

from argparse import ArgumentParser

import json
import sys

argparser = ArgumentParser(description='''\
  Each variable k becomes a package Xk with two conflicting versions, 0 and 1.
  Each clause {l1, ..., ln} becomes a dependency ¬l1→(l2 or ... or ln).
  The l1 is chosen arbitrarily, among the negative ones (fails if all positive).
''')
argparser.add_argument('cnf')
argparser.add_argument('json', help='gets overwritten')

def PV(index, version):
  return 'X{}={}'.format(index, version)

def P(index):
  return PV(-index, 0) if index < 0 else PV(index, 1)

def main():
  args = argparser.parse_args()
  repo = {}
  with open(args.cnf) as cnf_file:
    for line in cnf_file:
      line = line.strip()
      if line[:1] == '':
        continue
      elif line[:1] == 'p':
        ws = line.split()
        for i in range(int(ws[2])):
          repo[PV(i+1,0)] = { 'name' : 'X{}'.format(i+1), 'version' : '0', 'depends' : [], 'conflicts' : [PV(i+1,1)], 'size' : 1 }
          repo[PV(i+1,1)] = { 'name' : 'X{}'.format(i+1), 'version' : '1', 'depends' : [], 'size' : 1 }
      else:
        xs = [int(x) for x in line.split()]
        ns = [x for x in xs if x < 0]
        ps = [x for x in xs if x > 0]
        try:
          x, ns = ns[0], ns[1:]
        except IndexError:
          print('NO NEGATIVE')
          print('POS:',sorted(ps))
          print('NEG:',sorted(ns))
          sys.exit(1)
        ys = ps + ns
        repo[P(-x)]['depends'].append([P(y) for y in ys])
  with open(args.json, 'w') as jfile:
    json.dump(list(repo.values()), jfile)


if __name__ == '__main__':
  main()
