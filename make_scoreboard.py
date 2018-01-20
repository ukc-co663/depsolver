#!/usr/bin/env python3

import sys

def none_min(a, b):
  if a is None:
    return b
  if b is None:
    return a
  return min(a, b)

def main():
  with open('repos.txt') as f:
    users = f.read().split()
  seen_tests = ['seen-{}'.format(i) for i in range(10)]
  unseen_tests = ['unseen-{}'.format(i) for i in range(10)]
  tests = set(seen_tests + unseen_tests)
  costs = { u : { t : None for t in tests } for u in users }
  for u in users:
    ucosts = costs[u]
    with open('scoreboard/{}.log.txt'.format(u)) as f:
      test_name = None
      test_cost = None
      for line in f:
        if line.startswith('TEST'):
          if test_name is not None:
            ucosts[test_name] = test_cost
          test_name = line.split()[1].strip()
          test_cost = None
        elif line.startswith('cost'):
          test_cost = int(line.split()[1])
      if test_name is not None:
        ucosts[test_name] = test_cost
  min_cost = { t : None for t in tests }
  for t in tests:
    for u in users:
      min_cost[t] = none_min(min_cost[t], costs[u][t])
  points = { u : [] for u in users }
  for u in users:
    for t in seen_tests:
      score = 0
      if costs[u][t] is not None:
        score += 1
        score += min_cost[t] / costs[u][t]
      points[u].append(score)
    for t in unseen_tests:
      score = 0
      if costs[u][t] is not None:
        score += 1
      points[u].append(score)
  sys.stdout.write('<table class="scoreboard">\n')
  sys.stdout.write('<tr>\n')
  sys.stdout.write('  <th>Username</th>\n')
  sys.stdout.write('  <th>Marks</th>\n')
  for t in seen_tests + unseen_tests:
    sys.stdout.write('  <th>{}</th>\n'.format(t))
  sys.stdout.write('</tr>\n')
  for u, ps in sorted(points.items()):
    sys.stdout.write('<tr>\n')
    sys.stdout.write('  <td><b>{}</b></td>\n'.format(u))
    sys.stdout.write('  <td><b>{:.0f}</b></td>\n'.format(sum(ps)))
    for p in ps:
      sys.stdout.write('  <td>{:.3f}</td>\n'.format(p))
    sys.stdout.write('</tr>\n')
  sys.stdout.write('</table>\n')
  sys.stdout.write('<table>\n')
  sys.stdout.write('<tr>\n')
  sys.stdout.write('<th>Test</th>')
  sys.stdout.write('<th>MinCost</th>')
  sys.stdout.write('</tr>\n')
  for t in seen_tests + unseen_tests:
    sys.stdout.write('<tr><td>{}</td><td>{}</td></tr>\n'.format(t, min_cost[t]))
  sys.stdout.write('</table>\n')

if __name__ == '__main__':
  main()
