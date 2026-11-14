#!/usr/bin/env python3
"""Run historical whole-file substitutions in disposable archive trees.

This is evidence collection, not an automatic engineering-verification decision.
Files introduced by a commit have no parent version; their historical state is
absence, which is tested separately and never treated as a physics failure.
"""
import argparse
from concurrent.futures import ThreadPoolExecutor, as_completed
import json
import os
from pathlib import Path
import re
import subprocess
import tempfile

REPO = Path(__file__).resolve().parents[1]
BASE = 'ea77582'
CASES = [
 ('C1','2e3188a',['test_rolling_sphere_reference.py','test_optimization_conservative.py']),
 ('C2','19a607a',['test_touch_step_physics.py']),
 ('C3','1347b14',['test_lemp_heidler_physics.py','test_lemp_induction_physics.py']),
 ('C3','434a727',['test_lemp_heidler_physics.py','test_lemp_induction_physics.py']),
 ('C3-b','215c248',['test_lemp_induction_physics.py']),
 ('C3-b','6719bb9',['test_lemp_induction_physics.py']),
 ('C4','ec571e8',['test_rolling_sphere_edition2024.py']),
 ('C4-b','3343007',['test_minimum_length_l1_figure5.py']),
 ('H3','44ec813',['test_risk_factors_2024.py']),
 ('H4','16fa0ed',['test_multi_rod_mutual.py']),
 ('H5','dcc070d',['test_earthing_ring_strip.py']),
 ('H5','4235bd6',['test_earthing_ring_strip.py']),
 ('H8','3343007',['test_protective_angle_figure1.py']),
 ('H9','d7a2556',None),('H9','73c7cdc',None),('H9','70627fc',None),
 ('H9','dbb14da',None),('H9','bb20a92',None),('H9','a5b5bee',None),('H9','78d94c3',None),
 ('H15','b1114b2',['test_spd_coordination_annex_c.py']),
]

def git(*args):
 return subprocess.run(['git','-C',str(REPO),*args],stdout=subprocess.PIPE,stderr=subprocess.PIPE,check=True).stdout

def run_case(entry, pytest_path, h9):
 item, commit, path, tests = entry
 row = {'item':item,'commit':commit,'file':path,'adaptations':[], 'test_files':tests or h9}
 historic = subprocess.run(['git','-C',str(REPO),'show',f'{commit}^:{path}'],stdout=subprocess.PIPE,stderr=subprocess.PIPE)
 if historic.returncode:
  # Distinguish a file introduced by the fix from an unavailable object.
  exists = subprocess.run(['git','-C',str(REPO),'cat-file','-e',f'{commit}^:{path}'],stderr=subprocess.PIPE)
  if exists.returncode != 0 and subprocess.run(['git','-C',str(REPO),'cat-file','-e',f'{commit}^'],stderr=subprocess.PIPE).returncode == 0:
   row.update(kind='parent file absent', result='not run; file introduced by fix', failures=[], errors=[])
   return row
  raise RuntimeError(historic.stderr.decode(errors='replace'))
 with tempfile.TemporaryDirectory(prefix='step65-substitution-') as name:
  envarchive={**os.environ,'SCRATCH':name}
  subprocess.run('set -o pipefail; git archive ea77582 | tar -x -C "$SCRATCH"',cwd=REPO,env=envarchive,shell=True,executable='/bin/bash',check=True,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
  target=Path(name)/path
  if not target.is_file():
   row.update(kind='missing current file', result='not run; file absent from baseline', failures=[], errors=[])
   return row
  target.write_bytes(historic.stdout)
  env={**os.environ,'PYTHONPATH':os.pathsep.join(str(Path(name)/x) for x in ['services/calculation-engine','services/api','packages/domain-model','packages/geometry','packages/reporting','packages/standards-data']), 'PYTHONDONTWRITEBYTECODE':'1','OPENBLAS_NUM_THREADS':'1','OMP_NUM_THREADS':'1'}
  try:
   p=subprocess.run([str(pytest_path),'-q',*row['test_files']],cwd=name,env=env,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,text=True,timeout=90)
   text=p.stdout; lines=text.splitlines()
   fails=[x[7:].split(' - ')[0] for x in lines if x.startswith('FAILED ')]
   errors=[x[6:].split(' - ')[0] for x in lines if x.startswith('ERROR ')]
   exceptions=[x.strip() for x in lines if x.startswith('E   ')][:5]
   summary=[x.strip() for x in lines if re.search(r'\b(?:failed|passed|error|errors|xfailed)\b.*\bin \d',x)]
   row.update(kind='historical file', exit=p.returncode, result=summary[-1] if summary else f'exit {p.returncode}; no pytest summary', failures=fails, errors=errors, exceptions=exceptions)
  except subprocess.TimeoutExpired:
   row.update(kind='historical file', result='timed out after 90 s', failures=[], errors=[])
 # TemporaryDirectory cleaned even on errors.
 return row

def main():
 parser=argparse.ArgumentParser();parser.add_argument('--pytest',required=True);parser.add_argument('--jobs',type=int,default=4);parser.add_argument('--output',required=True);args=parser.parse_args()
 if args.jobs < 1 or args.jobs > 8: parser.error('--jobs must be between 1 and 8')
 before=git('status','--porcelain','-z')
 h9=sorted({l.strip() for l in git('show','--pretty=format:','--name-only','d7a2556','73c7cdc','70627fc','bb20a92','a5b5bee','78d94c3').decode().splitlines() if l.startswith('tests/test_') and l.endswith('.py')})
 entries=[]; empty=[]
 for item,commit,tests in CASES:
  paths=git('diff','--name-only',f'{commit}^',commit,'--','packages/','services/').decode().splitlines()
  if not paths: empty.append({'item':item,'commit':commit,'reason':'no code files in this commit'})
  for p in paths: entries.append((item,commit,p,None if tests is None else ['tests/'+t for t in tests]))
 results=[]
 with ThreadPoolExecutor(max_workers=args.jobs) as pool:
  futures={pool.submit(run_case,e,Path(args.pytest).resolve(strict=True),h9):e for e in entries}
  for future in as_completed(futures):
   result=future.result();results.append(result);print(f"{len(results)}/{len(entries)} {result['item']} {result['commit']} {result['file']}: {result['result']}",flush=True)
 order={(i,c,p):n for n,(i,c,p,_) in enumerate(entries)}
 results.sort(key=lambda r:order[(r['item'],r['commit'],r['file'])])
 if before != git('status','--porcelain','-z'): raise RuntimeError('Repository status changed during scratch checks')
 Path(args.output).write_text(json.dumps({'base':BASE,'results':results,'empty_commits':empty,'note':'Historical substitution evidence only. A failure may reflect later interface incompatibility, not a physics assertion. No adaptations were applied.'},indent=2)+'\n')
 print('scratch trees removed; repository status unchanged during checks',flush=True)

if __name__=='__main__': main()
