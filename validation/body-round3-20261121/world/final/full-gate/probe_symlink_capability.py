"""Record the existing Windows-only P1 test assumption without changing it."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import platform
import subprocess
import tempfile

parser=argparse.ArgumentParser()
parser.add_argument('--repo',type=Path,required=True)
parser.add_argument('--output',type=Path,required=True)
args=parser.parse_args()
test='tests/test_issue498_atomic_write_perm_symlink_guard.py'
baseline='6b73082406d40a630a44cd68559c1f66b3652390'
old=subprocess.check_output(['git','show',baseline+':'+test],cwd=args.repo).replace(b'\r\n',b'\n')
current=(args.repo/test).read_bytes().replace(b'\r\n',b'\n')
assert old==current
result={'os_name':os.name,'platform':platform.system(),'baseline':baseline,
        'test_source_identical_to_base':True,'test_sha256_lf':hashlib.sha256(current).hexdigest(),
        'failed_assertion':'P1 非 posix 上 symlink 竟成功（开发者模式？）——SKIP_LINK 可重核',
        'scope':'capability-only probe; no production code invoked or modified'}
with tempfile.TemporaryDirectory(prefix='own-symlink-capability-',dir=args.output.parent) as folder:
    root=Path(folder).resolve();assert root.is_relative_to(args.output.parent.resolve())
    real,link=root/'real.txt',root/'link.txt';real.write_text('owned-capability-probe',encoding='utf8')
    try:
        os.symlink(real,link)
    except OSError as error:
        result.update(symlink_created=False,errno=error.errno,winerror=getattr(error,'winerror',None),error=str(error))
    else:
        result.update(symlink_created=True,is_link=link.is_symlink(),contents_match=link.read_bytes()==real.read_bytes())
result['preexisting_test_assumption_conflicts_with_observed_capability']=(os.name!='posix' and result['symlink_created'])
args.output.write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf8',newline='\n')
print(json.dumps(result,ensure_ascii=False))
