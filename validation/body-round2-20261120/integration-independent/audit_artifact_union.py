"""Check guards, fixtures, benchmark/docs/tool contributions without edits."""
from collections import defaultdict
import json
from pathlib import Path
import audit_twelve_integration as A

incoming=defaultdict(list)
for pr,head in A.HEADS.items():
    ancestor=A.git('merge-base',A.BASE,head).strip()
    for path in A.git('diff','--name-only',ancestor,head).splitlines():
        incoming[path].append((pr,head,ancestor))
actual=set(A.git('diff','--name-only',A.BASE,A.HEAD).splitlines())
assert actual==set(incoming),(actual-set(incoming),set(incoming)-actual)
records=[]
folder=A.OUT/'artifact-reconstruction'
folder.mkdir(exist_ok=True)
for index,path in enumerate(sorted(actual)):
    if A.production(path) or path in ('docs/intake/body-export-v0.1/_export_manifest.json',
                                    'tools/time_core_lint_baseline.txt'):
        continue
    owners=incoming[path]
    if len(owners)==1:
        expected=A.blob(owners[0][1],path)
    else:
        try: expected=A.blob(A.BASE,path)
        except RuntimeError: expected=''
        for pr,head,ancestor in owners:
            try: base=A.blob(ancestor,path)
            except RuntimeError: base=''
            files=[folder/f'{index}-{kind}' for kind in ('current','base','incoming')]
            for file,text in zip(files,(expected,base,A.blob(head,path))):
                file.write_text(text,encoding='utf-8',newline='\n')
            run=A.command(['git','merge-file','-p',*map(str,files)],check=False)
            assert run.returncode==0,(path,pr,run.stderr)
            expected=run.stdout
    actual_text=A.blob(A.HEAD,path)
    assert expected==actual_text,(path,[p for p,_,_ in owners])
    records.append({'file':path,'owners':[p for p,_,_ in owners],
                    'lf_sha256':A.sha(actual_text),'exact_pr_contribution_union':True})
report={'verdict':'PASS','all_changed_paths':len(actual),'nonproduction_artifacts':len(records),
        'records':records,'source_and_two_registration_files':'independently checked by audit_twelve_integration.py'}
(A.OUT/'artifact-union.json').write_text(json.dumps(report,indent=2,ensure_ascii=False),encoding='utf-8')
print(json.dumps({k:v for k,v in report.items() if k!='records'},indent=2))
