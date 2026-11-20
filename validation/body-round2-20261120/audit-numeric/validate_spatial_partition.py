"""Run unchanged regression against baseline and isolated in-memory mutants."""
from __future__ import annotations
import json
import os
from pathlib import Path
import subprocess
import sys
import xml.etree.ElementTree as ET

OUT = Path(__file__).parent
FIXED = Path(r'[workspace]/lingshu/work\lingshu-body-spatial-partition-20261120')
BASE = Path(r'[workspace]/lingshu/work\lingshu-audit-core-20261120')
TEST = FIXED/'tests/test_spatial_detect_complete_partition.py'
COPY = OUT/TEST.name
COPY.write_bytes(TEST.read_bytes())
SOURCE = 'lingshu/nn/hex_text.py'


def run(name, repo, node='', mutation=None):
    xml = OUT/(name+'.xml')
    boot = '''import sys,json
from pathlib import Path
repo,test,xml,node,mutation=sys.argv[1:]
sys.path.insert(0,repo)
import lingshu.nn.hex_text as module
if mutation:
    change=json.loads(mutation)
    source=Path(repo)/"lingshu/nn/hex_text.py"
    raw=source.read_text(encoding="utf-8")
    assert raw.count(change["old"])==1, "mutation target is not unique"
    exec(compile(raw.replace(change["old"],change["new"],1),str(source),"exec"),module.__dict__)
import pytest
raise SystemExit(pytest.main([test+("::"+node if node else ""),"-q","-p","no:cacheprovider","--confcutdir",str(Path(test).parent),"--junitxml",xml]))
'''
    result = subprocess.run([sys.executable,'-X','utf8','-B','-c',boot,str(repo),str(COPY),str(xml),node,
                             json.dumps(mutation) if mutation else ''],cwd=OUT,
                            env={**os.environ,'PYTHONDONTWRITEBYTECODE':'1'},
                            capture_output=True,text=True,encoding='utf-8',errors='replace')
    log = result.stdout + result.stderr
    (OUT/(name+'.log')).write_text(log,encoding='utf-8')
    root = ET.parse(xml).getroot()
    suite = root.find('testsuite')
    return {'name':name,'returncode':result.returncode,'tests':int(suite.get('tests')),
            'failures':int(suite.get('failures')),'errors':int(suite.get('errors')),
            'skipped':int(suite.get('skipped')),'log':log}


def main():
    baseline=run('spatial-baseline',BASE)
    fixed=run('spatial-fixed-isolated',FIXED)
    spec=json.loads((FIXED/'tests/fixtures/spatial_detect_complete_partition_mutations.json').read_text(encoding='utf-8'))
    result=[]
    for change in spec['mutations']:
        r=run('mutation-'+change['name'],FIXED,change['test'],change)
        r['killed']=(r['returncode']==1 and r['tests']==1 and r['failures']==1 and
                     r['errors']==0 and r['skipped']==0 and change['assertion'] in r['log'])
        r.pop('log')
        result.append(r)
        print(r,flush=True)
    baseline.pop('log'); fixed.pop('log')
    summary={'baseline':baseline,'fixed':fixed,'mutations':result,
             'verdict':baseline['failures']>0 and fixed['returncode']==0 and all(r['killed'] for r in result)}
    (OUT/'spatial-validation.json').write_text(json.dumps(summary,indent=2),encoding='utf-8')
    print(json.dumps(summary,indent=2))
    return 0 if summary['verdict'] else 1


if __name__=='__main__':
    raise SystemExit(main())
