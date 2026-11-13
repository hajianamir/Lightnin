#!/usr/bin/env python3
"""Check complete inverse code diffs in disposable ec54036 trees (no partial patches)."""
import argparse
import os
from pathlib import Path
import re
import subprocess
import tarfile
import tempfile
import io

REPO = Path(__file__).resolve().parents[1]
BASE = 'ec54036'
CASES = [
    ('C1', '2e3188a', ['test_rolling_sphere_reference.py', 'test_optimization_conservative.py']),
    ('C2', '19a607a', ['test_touch_step_physics.py']),
    ('C3', '1347b14', ['test_lemp_heidler_physics.py', 'test_lemp_induction_physics.py']),
    ('C3 follow-up', '434a727', ['test_lemp_heidler_physics.py', 'test_lemp_induction_physics.py']),
    ('C3-b', '215c248', ['test_lemp_induction_physics.py']),
    ('C3-b follow-up', '6719bb9', ['test_lemp_induction_physics.py']),
    ('C4', 'ec571e8', ['test_rolling_sphere_edition2024.py']),
    ('C4-b', '3343007', ['test_minimum_length_l1_figure5.py']),
    ('H3', '44ec813', ['test_risk_factors_2024.py']),
    ('H4', '16fa0ed', ['test_multi_rod_mutual.py']),
    ('H5', 'dcc070d', ['test_earthing_ring_strip.py']),
    ('H5 follow-up', '4235bd6', ['test_earthing_ring_strip.py']),
    ('H8', '3343007', ['test_protective_angle_figure1.py']),
    ('H9 B1', 'd7a2556', None), ('H9 B2', '73c7cdc', None),
    ('H9 B3', '70627fc', None), ('H9 B3 baseline', 'dbb14da', None),
    ('H9 B4', 'bb20a92', None), ('H9 B5', 'a5b5bee', None),
    ('H9 B6', '78d94c3', None),
    ('H15', 'b1114b2', ['test_spd_coordination_annex_c.py']),
]

def git(*args, **kw):
    return subprocess.run(['git', '-C', str(REPO), *args], stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True, **kw).stdout

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--pytest', required=True, help='absolute path to pytest in an external virtualenv')
    args = parser.parse_args()
    pytest = Path(args.pytest).resolve(strict=True)
    before = git('status', '--porcelain', '-z')
    tests_h9 = sorted({line.strip() for line in git('show', '--pretty=format:', '--name-only', 'd7a2556', '73c7cdc', '70627fc', 'bb20a92', 'a5b5bee', '78d94c3', text=True).splitlines() if line.startswith('tests/test_') and line.endswith('.py')})
    tar = git('archive', BASE)
    print('# Step 6.4 full inverse-diff checks\n')
    print(f'Baseline: `{BASE}`; pytest: `{pytest}`. Each commit is tested independently in a fresh archive. Code means all changed files under `packages/` and `services/`; test and baseline changes are excluded. No rejected or partial hunks are applied.\n')
    print('| Item | Fix | Code files | Total hunks | Reverted hunks | Result |')
    print('|---|---|---|---:|---:|---|')
    details = []
    for item, commit, tests in CASES:
        # Confirm the commit and enumerate every code change, including newly created files.
        git('cat-file', '-e', f'{commit}^{{commit}}')
        diff = git('diff', '--binary', f'{commit}^', commit, '--', 'packages/', 'services/')
        files = git('diff', '--name-only', f'{commit}^', commit, '--', 'packages/', 'services/', text=True).splitlines()
        hunks = len(re.findall(rb'^@@ ', diff, re.MULTILINE))
        tests = tests_h9 if tests is None else ['tests/' + x for x in tests]
        if not diff:
            print(f'| {item} | `{commit}` | none | 0 | 0 | No code diff; baseline-only commit. |')
            continue
        with tempfile.TemporaryDirectory(prefix='step64-inverse-') as name:
            scratch = Path(name)
            with tarfile.open(fileobj=io.BytesIO(tar)) as archive:
                for member in archive.getmembers():
                    if member.issym() or member.islnk() or not (scratch / member.name).resolve().is_relative_to(scratch):
                        raise ValueError(f'Unsafe archive member: {member.name}')
                archive.extractall(scratch)
            check = subprocess.run(['git', 'apply', '--whitespace=nowarn', '--reverse', '--check', '-'], input=diff, cwd=scratch, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            if check.returncode:
                diagnostic = check.stderr.decode(errors='replace').strip()
                print(f'| {item} | `{commit}` | {len(files)} | {hunks} | 0 | **partial / not applied**; reverse check failed, tests not run. |')
                details.append((item, commit, files, hunks, tests, 'Reverse check errors', diagnostic))
                continue
            subprocess.run(['git', 'apply', '--whitespace=nowarn', '--reverse', '-'], input=diff, cwd=scratch, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            env = dict(os.environ)
            env['PYTHONPATH'] = os.pathsep.join(str(scratch / p) for p in ('services/calculation-engine', 'services/api', 'packages/domain-model', 'packages/geometry', 'packages/reporting', 'packages/standards-data'))
            env['PYTHONDONTWRITEBYTECODE'] = '1'
            test = subprocess.run([str(pytest), '-q', *tests], cwd=scratch, env=env, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
            failure_lines = [line for line in test.stdout.splitlines() if line.startswith(('FAILED ', 'ERROR '))]
            summaries = [line for line in test.stdout.splitlines() if re.search(r'\b(?:failed|passed|error|errors|xfailed)\b.*\bin \d', line)]
            summary = summaries[-1] if summaries else f'pytest exit {test.returncode}; no summary'
            print(f'| {item} | `{commit}` | {len(files)} | {hunks} | {hunks} | Full inverse applied; {summary.replace("|", "/")}. |')
            details.append((item, commit, files, hunks, tests, 'Pytest failing/error names', '\n'.join(failure_lines) or '(none)'))
        assert not scratch.exists(), 'scratch cleanup failed'
    print('\n## Files, commands and diagnostics\n')
    for item, commit, files, hunks, tests, label, output in details:
        print(f'### {item} — `{commit}`\n')
        print(f'Files ({len(files)}), {hunks} total hunks: ' + ', '.join(f'`{x}`' for x in files))
        print(f'\nPatch: `git diff {commit}^ {commit} -- packages/ services/` → `git apply --whitespace=nowarn --reverse --check -` and, only if clean, `git apply --whitespace=nowarn --reverse -`.')
        print('\nPinning files: ' + ', '.join(f'`{x}`' for x in tests))
        print(f'\n{label}:\n\n```text\n{output}\n```\n')
    after = git('status', '--porcelain', '-z')
    if before != after:
        raise RuntimeError('Repository status changed during scratch verification')
    print('All scratch trees removed; repository status unchanged by the checks.')

if __name__ == '__main__':
    main()
