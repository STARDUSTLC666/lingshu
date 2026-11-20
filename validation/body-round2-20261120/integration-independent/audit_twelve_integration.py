"""Read-only independent exact-head/AST/source/manifest/lint integration audit."""
from __future__ import annotations

import ast
from collections import Counter, defaultdict
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import re
import subprocess
import sys

ROOT=Path(r'[workspace]')
OUT=Path(__file__).parent
BASE='d74848fb33dbff1d719959df19d1266a1ac60f44'
HEAD='5226860c1d70bc7fc6619cf79aff10c4f9a2a234'
TREE='529e1e150aa2c05a2f5bee3126c4678a58695e21'
HEADS={
 1469:'cc68a82baace16e92ff6ce770330b65102a530a5',
 1470:'433befa7b356eebecbc457ecd8f8a123ec1540cc',
 1471:'39d379552f34026ef46ad0515831319b1494a5d3',
 1472:'a663512dd0fbc44a9fb08a55751951009586d172',
 1473:'cff189b3438623feaebdf1a874fafdd03080acb1',
 1474:'fb6c9cabc939a6defcc44ef661b3048d47155d87',
 1475:'e0771a810b8846676f3545542b2e70d5e0011467',
 1476:'1ab5cc7f295ed5748b50c7ffde26cf2a34663204',
 1477:'e821bbb1fac57fa638640e3caf153caf7f1b1973',
 1478:'89c005b7fdd48f64c603d34c280a4d18a93956f7',
 1479:'13952c82874fb9ee19a4f1b660e3144134367a53',
 1480:'a357dbbe96905848fd81b7249814576fb2743674',
}


def command(args, check=True):
    run=subprocess.run(args,cwd=ROOT,capture_output=True,text=True,
                       encoding='utf-8',errors='strict')
    if check and run.returncode:
        raise RuntimeError((args,run.returncode,run.stdout,run.stderr))
    return run


def git(*args): return command(['git',*args]).stdout
def blob(ref,path): return git('show',f'{ref}:{path}')
def sha(text): return hashlib.sha256(text.encode('utf-8')).hexdigest()
def production(path): return path.endswith('.py') and path.startswith(('lingshu/','bridges/'))


def definitions(source):
    result={}
    def visit(body,prefix=''):
        for node in body:
            if isinstance(node,(ast.FunctionDef,ast.AsyncFunctionDef,ast.ClassDef)):
                name=prefix+node.name
                if not isinstance(node,ast.ClassDef):
                    result[name]={'ast':ast.dump(node,include_attributes=False),
                                  'text':ast.get_source_segment(source,node),
                                  'line':node.lineno}
                visit(node.body,name+'.')
    visit(ast.parse(source).body)
    return result


def manifest_records(payload):
    rows={}
    if isinstance(payload.get('blocks'),dict):
        for block,value in payload['blocks'].items():
            for row in value['files']:
                path=f"lingshu/{block}/{row['file']}"
                assert path not in rows,path
                rows[path]=row
    else:
        for key in ('artifacts','tests'):
            for row in payload.get(key,[]):
                path=row['file']
                assert path not in rows,path
                rows[path]=row
    return rows


def lint_rows(ref):
    text=blob(ref,'tools/time_core_lint_baseline.txt')
    rows=[]
    for line in text.splitlines():
        found=re.match(r'^([^#\s].*?):(\d+):(R\d+)\s*(.*)$',line)
        if found:
            path,number,rule,comment=found.groups()
            code=blob(ref,path).splitlines()[int(number)-1].strip()
            rows.append({'path':path,'line':int(number),'rule':rule,'code':code,'comment':comment})
    return rows,text


def main():
    initial_status=git('status','--porcelain=v1')
    assert not initial_status,initial_status
    assert git('rev-parse','HEAD').strip()==HEAD
    assert git('rev-parse','HEAD^{tree}').strip()==TREE
    raw=json.loads(command(['gh','api','repos/FuRongJun-1999/lingshu/pulls?state=open&per_page=100']).stdout)
    remote={p['number']:p for p in raw if p['number'] in HEADS}
    remote_report=[]
    for pr,head in HEADS.items():
        p=remote[pr]
        assert p['head']['sha']==head,(pr,p['head']['sha'])
        assert p['base']['sha']==BASE,(pr,p['base']['sha'])
        remote_report.append({'pr':pr,'head':head,'base':p['base']['sha'],'state':p['state'],
                              'url':p['html_url'],'title':p['title']})
    (OUT/'exact-pr-heads.json').write_text(json.dumps(remote_report,indent=2,ensure_ascii=False),encoding='utf-8')

    actual_paths=set(filter(production,git('diff','--name-only',BASE,HEAD).splitlines()))
    incoming=defaultdict(list)
    function_owners=defaultdict(list)
    per_pr=[]
    for pr,head in HEADS.items():
        # A PR is its three-dot contribution, not a two-dot diff that also
        # reverses target-only commits. PR1469 predates d748's camera fix.
        contribution_base=git('merge-base',BASE,head).strip()
        paths=list(filter(production,git('diff','--name-only',contribution_base,head).splitlines()))
        funcs=[]
        (OUT/f'pr-{pr}-production.patch').write_text(git('diff',contribution_base,head,'--',*paths),encoding='utf-8')
        for path in paths:
            old,new=blob(contribution_base,path),blob(head,path)
            incoming[path].append((pr,new,old))
            before,after=definitions(old),definitions(new)
            for key in sorted(set(before)|set(after)):
                a,b=before.get(key),after.get(key)
                if (a or {}).get('ast')!=(b or {}).get('ast'):
                    function_owners[(path,key)].append(pr)
                    funcs.append({'file':path,'function':key,'kind':'added' if a is None else 'deleted' if b is None else 'modified',
                                  'pr_ast_sha256':sha(b['ast']) if b else None,
                                  'pr_text_sha256':sha(b['text']) if b else None})
        per_pr.append({'pr':pr,'head':head,'contribution_base':contribution_base,
                       'production_files':paths,'changed_functions':funcs})
    assert actual_paths==set(incoming),(actual_paths,set(incoming))
    files=[]
    folder=OUT/'three-way-reconstruction'
    folder.mkdir(exist_ok=True)
    for index,path in enumerate(sorted(actual_paths)):
        baseline=blob(BASE,path)
        merged=baseline
        steps=[]
        for pr,text,contribution_base_text in incoming[path]:
            a,b,c=folder/f'{index}-current.py',folder/f'{index}-base.py',folder/f'{index}-incoming.py'
            a.write_text(merged,encoding='utf-8',newline='\n')
            b.write_text(contribution_base_text,encoding='utf-8',newline='\n')
            c.write_text(text,encoding='utf-8',newline='\n')
            run=command(['git','merge-file','-p',str(a),str(b),str(c)],check=False)
            assert run.returncode==0,(path,pr,run.returncode,run.stderr)
            merged=run.stdout
            steps.append({'pr':pr,'merged_lf_sha256':sha(merged)})
        actual=blob(HEAD,path)
        worktree=(ROOT/path).read_bytes().replace(b'\r\n',b'\n').decode('utf-8')
        assert actual==worktree,(path,'worktree differs from Git blob')
        assert merged==actual,(path,'not the exact independent PR union')
        (folder/f'{index}-expected.py').write_text(merged,encoding='utf-8',newline='\n')
        files.append({'file':path,'owners':[pr for pr,_,_ in incoming[path]],'steps':steps,
                      'merged_lf_sha256':sha(merged),'actual_lf_sha256':sha(actual),'byte_exact_union':True})
    function_report=[]
    for (path,key),owners in sorted(function_owners.items()):
        actual=definitions(blob(HEAD,path)).get(key)
        if len(owners)==1:
            target=definitions(blob(HEADS[owners[0]],path)).get(key)
            ast_same=(actual or {}).get('ast')==(target or {}).get('ast')
            text_same=(actual or {}).get('text')==(target or {}).get('text')
            assert ast_same and text_same,(path,key,owners)
        else:
            ast_same=text_same=None
        function_report.append({'file':path,'function':key,'owners':owners,
                                'single_owner_ast_exact':ast_same,'single_owner_text_exact':text_same,
                                'merged_source_union_exact':True})

    manifests=[]
    manifest_paths=git('ls-tree','-r','--name-only',HEAD,'docs/intake').splitlines()
    for path in filter(lambda p:p.endswith('/_export_manifest.json'),manifest_paths):
        records=manifest_records(json.loads(blob(HEAD,path)))
        old_records=manifest_records(json.loads(blob(BASE,path)))
        assert set(records)==set(old_records)
        for name,row in records.items():
            text=(ROOT/name).read_bytes().replace(b'\r\n',b'\n')
            actual_hash=hashlib.sha256(text).hexdigest()
            assert actual_hash.startswith(row['sha256']),(path,name)
            if 'bytes' in row: assert row['bytes']==len(text),(name,row['bytes'],len(text))
            assert {k:v for k,v in row.items() if k not in ('sha256','bytes')}=={
                k:v for k,v in old_records[name].items() if k not in ('sha256','bytes')},(path,name,'unrelated manifest metadata change')
            manifests.append({'manifest':path,'source':name,'recorded_sha256':row['sha256'],
                              'actual_lf_sha256':actual_hash,'lf_bytes':len(text),'ok':True})
    assert len(manifests)==64,len(manifests)
    old_lint,old_text=lint_rows(BASE)
    new_lint,new_text=lint_rows(HEAD)
    def multiset(rows): return Counter((r['path'],r['rule'],r['code'],r['comment']) for r in rows)
    assert len(old_lint)==len(new_lint)==23
    assert multiset(old_lint)==multiset(new_lint),'exemption semantic statement multiset changed'
    old_comments=[line for line in old_text.splitlines() if line.startswith('#')]
    assert all(line in new_text.splitlines() for line in old_comments),'historical baseline comments removed'
    lint_run=command([sys.executable,'-X','utf8','-B','tools/time_core_lint.py','--json'])
    (OUT/'time-core-lint.json').write_text(lint_run.stdout,encoding='utf-8')
    lint_json=json.loads(lint_run.stdout)
    assert lint_json.get('exit_code')==0,lint_json
    assert git('status','--porcelain=v1')==initial_status
    assert git('rev-parse','HEAD').strip()==HEAD
    report={'date_utc':datetime.now(timezone.utc).isoformat(),'base':BASE,'head':HEAD,'tree':TREE,
            'remote_pr_heads':remote_report,'production_files':files,'per_pr':per_pr,
            'changed_function_ownership':function_report,'manifest_records':manifests,
            'time_baseline':{'before':old_lint,'after':new_lint,'count':23,
                             'same_source_statement_multiset':True,'historical_comments_preserved':True},
            'status_before':initial_status,'status_after':git('status','--porcelain=v1'),
            'verdict':'PASS'}
    (OUT/'audit-summary.json').write_text(json.dumps(report,indent=2,ensure_ascii=False),encoding='utf-8')
    print(json.dumps({'verdict':'PASS','production_files':len(files),'prs':len(HEADS),
                      'changed_functions':len(function_report),'multi_owner_functions':[
                          x for x in function_report if len(x['owners'])>1],
                      'manifest_records':len(manifests),'time_exemptions':len(new_lint)},indent=2))


if __name__=='__main__': main()
