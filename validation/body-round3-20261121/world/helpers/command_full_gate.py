from __future__ import annotations
import argparse
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import time
import xml.etree.ElementTree as ET
import yaml

parser = argparse.ArgumentParser()
parser.add_argument('--repo', type=Path, required=True)
parser.add_argument('--output', type=Path, required=True)
parser.add_argument('--brain', type=Path, required=True)
parser.add_argument('--baseline-tree', type=Path, required=True)
args = parser.parse_args()
root, output = args.repo.resolve(), args.output.resolve()
output.mkdir(parents=True, exist_ok=True)
scripts = yaml.safe_load((root/'.github/workflows/gate.yml').read_text(encoding='utf8'))['env']['SCRIPT_TESTS'].split()
env = dict(os.environ, PYTHONDONTWRITEBYTECODE='1', PYTHONUTF8='1', PYTHONIOENCODING='utf-8',
           PYTHONPATH=str(root), MDCG_BRAIN_PYTHONPATH=str(args.brain.resolve()),
           LINGSHU_BASE_TREE=str(args.baseline_tree.resolve()))
records = []

def run(name, command, timeout):
    before = time.perf_counter()
    try:
        proc = subprocess.run(command, cwd=root, env=env, capture_output=True, timeout=timeout)
        stdout, stderr, code = proc.stdout, proc.stderr, proc.returncode
    except subprocess.TimeoutExpired as error:
        stdout, stderr, code = error.stdout or b'', error.stderr or b'', -999
    (output/(name+'.stdout.log')).write_bytes(stdout)
    (output/(name+'.stderr.log')).write_bytes(stderr)
    record = dict(name=name, command=command, exit_code=code, elapsed_seconds=time.perf_counter()-before,
                  stdout_sha256=hashlib.sha256(stdout).hexdigest(), stderr_sha256=hashlib.sha256(stderr).hexdigest(),
                  stdout_bytes=len(stdout), stderr_bytes=len(stderr),
                  last_lines=(stdout+stderr).decode('utf8',errors='replace').splitlines()[-4:])
    records.append(record)
    print(json.dumps(record, ensure_ascii=False), flush=True)
    (output/'commands-progress.json').write_text(json.dumps(records,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
    return record

for index, script in enumerate(scripts):
    run(f'script-{index+1:03d}-'+Path(script).stem, [sys.executable,'-B','-X','utf8',script], 300)
junit = output/'pytest.xml'
command = [sys.executable,'-B','-X','utf8','-m','pytest','tests/','-q','-n','4','--dist','loadfile',
           '--junitxml='+str(junit), *['--ignore='+p for p in scripts]]
run('pytest', command, 2400)
for name, command in [('manifest',[sys.executable,'-B','-X','utf8','tools/verify_manifest.py','--strict','--json']),
                      ('time-core',[sys.executable,'-B','-X','utf8','tools/time_core_lint.py','--json'])]:
    run(name, command, 180)
summary = dict(head=subprocess.check_output(['git','rev-parse','HEAD'],cwd=root,text=True).strip(),
               source_sha256_lf=hashlib.sha256((root/'lingshu/world/scene_simulator.py').read_bytes().replace(b'\r\n',b'\n')).hexdigest(),
               pinned_brain_head=subprocess.check_output(['git','-C',str(args.brain),'rev-parse','HEAD'],text=True).strip(),
               frozen_physics_baseline='124ea433fe9a2ad2fd66a7360df85f6d61bab793',
               scripts=len(scripts), all_commands_exit_zero=all(r['exit_code']==0 for r in records), records=records)
if junit.exists():
    cases=ET.parse(junit).findall('.//testcase')
    summary['pytest']={'testcases':len(cases),'failures':sum(c.find('failure') is not None for c in cases),
                       'errors':sum(c.find('error') is not None for c in cases),'skipped':sum(c.find('skipped') is not None for c in cases)}
(output/'summary.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
print(json.dumps({k:v for k,v in summary.items() if k!='records'},ensure_ascii=False),flush=True)
raise SystemExit(0 if summary['all_commands_exit_zero'] else 1)
