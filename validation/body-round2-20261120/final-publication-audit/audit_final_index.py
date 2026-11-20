"""Independent read-only Git-index evidence and semantic publication audit."""
from __future__ import annotations
import ast
from collections import Counter
from datetime import datetime, timezone
import hashlib
import json
import math
from pathlib import Path
import re
import subprocess
import sys
import xml.etree.ElementTree as ET

ROOT=Path(r'[workspace]/lingshu/work\lingshu-body-round2-evidence-final-20261121')
RAW=Path(r'[workspace]/lingshu/outputs\body-round2-20261120')
OUT=Path(__file__).parent
PREFIX='validation/body-round2-20261120/'
HEAD='ff22bf03a53e422fedc029fbd0d24445aef3dbe7'
SOURCE='5226860c1d70bc7fc6619cf79aff10c4f9a2a234'
BASE='d74848fb33dbff1d719959df19d1266a1ac60f44'
DETACHED={'final-seal-audit.json','preparation-audit.json','sanitization-manifest.json'}
PRIVATE=re.compile(r'(?:[Ee]:[\\/]+(?:lingshu|deepseek|公益站)|[Cc]:[\\/]+Users[\\/]+29022)',re.I)


def git(*args):
    return subprocess.run(['git',*args],cwd=ROOT,capture_output=True,check=True).stdout


def digest(data): return hashlib.sha256(data).hexdigest()


def load_index():
    raw=git('ls-files','-s','-z','--',PREFIX)
    entries=[]
    for item in raw.split(b'\0'):
        if not item: continue
        meta,path=item.split(b'\t',1)
        mode,oid,stage=meta.split()
        assert stage==b'0',(path,stage)
        entries.append((path.decode('utf-8'),oid.decode()))
    oids=list(dict.fromkeys(o for _,o in entries))
    data=subprocess.run(['git','cat-file','--batch'],cwd=ROOT,
                        input=('\n'.join(oids)+'\n').encode(),capture_output=True,check=True).stdout
    objects={}; at=0
    for oid in oids:
        end=data.index(b'\n',at)
        got,kind,size=data[at:end].decode().split(); size=int(size); at=end+1
        assert got==oid and kind=='blob'
        objects[oid]=data[at:at+size]; at+=size+1
    return raw,{p[len(PREFIX):]:objects[o] for p,o in entries},dict(entries)


def junit_summary(data):
    root=ET.fromstring(data)
    tests=root.findall('.//testcase')
    failures=[t for t in tests if t.find('failure') is not None]
    errors=[t for t in tests if t.find('error') is not None]
    skipped=[t for t in tests if t.find('skipped') is not None]
    return {'testcases':len(tests),'passed':len(tests)-len(failures)-len(errors)-len(skipped),
            'failures':len(failures),'errors':len(errors),'skipped':len(skipped),
            'reported_tests':sum(int(s.get('tests',0)) for s in root.findall('.//testsuite')),
            'failed_names':[t.get('name') for t in failures]}


def numeric_tree(value):
    # Object order is retained by the sanitizer; ignore path text, including
    # keys, but compare every numeric/bool/null value and structural shape.
    if isinstance(value,dict): return ('object',tuple(numeric_tree(v) for v in value.values()))
    if isinstance(value,list): return ('array',tuple(numeric_tree(v) for v in value))
    if isinstance(value,bool): return ('bool',value)
    if isinstance(value,(int,float)):
        if isinstance(value,float) and math.isnan(value): return ('number','nan')
        return ('number',value)
    if value is None: return ('null',)
    return ('string',)


def numeric_count(value):
    if isinstance(value,dict): return sum(numeric_count(v) for v in value.values())
    if isinstance(value,list): return sum(numeric_count(v) for v in value)
    return int(isinstance(value,(int,float)))


def main():
    assert git('rev-parse','HEAD').decode().strip()==HEAD
    index_before,files,index_paths=load_index()
    manifest=json.loads(files['sanitization-manifest.json'])
    records={r['artifact']:r for r in manifest['artifacts']}
    assert len(records)==len(manifest['artifacts'])==1580
    assert len(files)==1583
    assert set(files)-set(records)==DETACHED
    assert not set(records)-set(files)
    checked=[]; parse_counts=Counter(); private=[]; forbidden=[]; numeric_rows=[]; mutable_raw_drift=[]
    for path,data in files.items():
        if path in records:
            row=records[path]
            for key in ('published_sha256','git_canonical_blob_sha256'):
                assert row[key]==digest(data),(path,key)
            for key in ('published_bytes','git_canonical_blob_bytes'):
                assert row[key]==len(data),(path,key)
            checked.append({'artifact':path,'sha256':digest(data),'bytes':len(data),
                            'git_blob':index_paths[PREFIX+path]})
        parts=set(Path(path).parts)
        if (any(x in parts for x in ('__pycache__','.pytest_cache','.git','.mypy_cache','.ruff_cache'))
                or re.search(r'\.(?:pyc|pyo|db|sqlite|sqlite3)(?:-(?:wal|shm))?$',path,re.I)
                or Path(path).name in ('index','index.lock')):
            forbidden.append(path)
        text=data.decode('utf-8',errors='replace')
        if PRIVATE.search(text): private.append(path)
        if path.endswith('.json'):
            parsed=json.loads(data); parse_counts['json']+=1
            if path in records and records[path].get('source'):
                source=RAW/records[path]['source']
                if source.is_file():
                    original=source.read_bytes()
                    if digest(original)!=records[path]['original_sha256'] or len(original)!=records[path]['original_bytes']:
                        mutable_raw_drift.append(path)
                        continue
                    try: raw_parsed=json.loads(original)
                    except (json.JSONDecodeError,UnicodeDecodeError): continue
                    if records[path]['mode']=='sanitized_verbatim_numeric_preserving':
                        assert numeric_tree(parsed)==numeric_tree(raw_parsed),(path,'numeric/structural mutation')
                        numeric_rows.append({'artifact':path,'numeric_bool_leaves':numeric_count(parsed)})
        elif path.endswith('.xml'):
            ET.fromstring(data); parse_counts['xml']+=1
        if path.startswith('tools/') and path.endswith('.py'):
            ast.parse(data.decode('utf-8')); parse_counts['control_python']+=1
    assert not private,private
    assert not forbidden,forbidden
    assert parse_counts['xml']==314,parse_counts
    # Former residuals were JSON object keys, so check the keys explicitly.
    win=json.loads(files['integration-windows/summary.json'])
    assert all(not PRIVATE.search(k) for k in win['skip_reasons'])
    assert win['head']==SOURCE and win['gate_ok'] is False
    totals=junit_summary(files['integration-windows/pytest.xml'])
    assert totals['failures']==1 and totals['errors']==0 and totals['skipped']==28
    assert totals['passed']==5838,totals
    assert totals['reported_tests']-totals['testcases']==98,totals
    assert 'test_p1_符号链接量具能力探测' in totals['failed_names'][0]
    raw_win=(RAW/'integration-final-r2/summary.json')
    compare=json.loads(files['integration-windows/windows-final-comparison.json'])
    assert compare['gate_ok'] is False and compare['source']==compare['source_after']==SOURCE
    raw_log=files['integration-windows/pytest_full.log'].decode('utf-8')
    assert re.search(r'5838 passed',raw_log) and re.search(r'98 subtests passed',raw_log),raw_log[-1200:]
    assert len(win['script_results'])==102 and all(r['returncode']==0 for r in win['script_results'])

    # Receipts are checked against their actual intake header and exact head.
    receipts=json.loads(files['publication-receipts/intake-receipts.json'])
    mappings=[]
    expected_heads={1477:'e821bbb1fac57fa638640e3caf153caf7f1b1973',
                    1478:'89c005b7fdd48f64c603d34c280a4d18a93956f7',
                    1479:'13952c82874fb9ee19a4f1b660e3144134367a53',
                    1480:'a357dbbe96905848fd81b7249814576fb2743674'}
    for pr,head in expected_heads.items():
        row=receipts[str(pr)]
        assert row['source_head']==head and row['issue_number']==pr+1314
        assert row['pr']==f'https://github.com/FuRongJun-1999/lingshu/pull/{pr}'
        assert row['issue_url']==f'https://github.com/FuRongJun-1999/dsh-bounty/issues/{pr+1314}'
        body=files[f'publication-receipts/intake-{pr}.md'].decode('utf-8')
        marker=re.search(r'<!-- intake:v1 (\{.*?\}) -->',body)
        assert marker and json.loads(marker.group(1))['pr']==row['pr']
        assert head in body
        mappings.append({'pr':pr,'intake':pr+1314,'head':head})

    combined=json.loads(files['remote-ci/combined/summary.json'])
    assert combined['expected_head']==combined['actual_run_head']==SOURCE
    assert combined['all_complete'] and combined['all_success'] and combined['conclusion']=='success'
    linux=[]
    for job in combined['jobs']:
        jid=job['job_id']
        data=json.loads(files[f'remote-ci/combined/{jid}-summary.json'])
        assert data['head_sha']==SOURCE and data['conclusion']=='success'
        log=files[f'remote-ci/combined/{jid}.log'].decode('utf-8')
        found=re.search(r'5827 passed(?:, |.*?)(?:40 skipped)',log)
        assert found,(jid,'no original pytest success line')
        assert '98 subtests passed' in log
        assert data['script_groups']==data['unique_scripts']==102 and data['scripts_match_workflow']
        linux.append({'job_id':jid,'passed':5827,'skipped':40,'subtests':98})
    assert len(linux)==3

    final_root='linux-benchmarks/final-44778606930/'
    bench=json.loads(files[final_root+'summary.json'])
    assert bench['run_id']==44778606930 and bench['metadata_head']==HEAD and bench['measured_source_head']==SOURCE
    assert bench['all_complete'] and bench['all_verified_success'] and bench['inner_artifact_indexes_clean']
    inners=sorted(p for p in files if p.startswith(final_root+'artifacts/') and p.endswith('/artifact-index.json'))
    assert len(inners)==3
    matrices=[]
    family_specs={'core':'fresh_row_decay_mutations.json','circular':'circular_time_residual_mutations.json',
                  'numeric':'spatial_detect_complete_partition_mutations.json','world':'scene_collision_freeflight_velocity_mutations.json'}
    spec_blobs={k:json.loads(git('show',f'{SOURCE}:tests/fixtures/{v}')) for k,v in family_specs.items()}
    def source_blob(ref,path): return git('show',f'{ref}:{path}')
    for ipath in inners:
        directory=ipath.rsplit('/',1)[0]+'/'
        inner=json.loads(files[ipath]); rows=inner['files']
        assert len(rows) in (136,137)
        source_index_path=RAW/records[ipath]['source']
        assert source_index_path.is_file()
        original_index=json.loads(source_index_path.read_bytes())
        assert inner==original_index,'published raw artifact index was rewritten'
        assert len({r['path'] for r in rows})==len(rows)
        raw_hashes=[]
        for row in rows:
            raw_path=source_index_path.parent/row['path']
            assert raw_path.is_file(),(ipath,row['path'])
            data=raw_path.read_bytes()
            assert len(data)==row['bytes'] and digest(data)==row['sha256'],(ipath,row['path'],'inner original mismatch')
            artifact=directory+row['path']
            assert artifact in records
            assert records[artifact]['original_sha256']==row['sha256'] and records[artifact]['original_bytes']==row['bytes']
            raw_hashes.append({'path':row['path'],'sha256':digest(data),'bytes':len(data)})
        provenance=json.loads(files[directory+'provenance.json'])
        assert provenance['source_sha']==SOURCE and provenance['baseline_sha']==BASE
        assert provenance['github_run']['GITHUB_SHA']==HEAD
        assert provenance['github_run']['GITHUB_RUN_ID']=='44778606930'
        for path,h in provenance['input_files_sha256'].items():
            ref=HEAD if path.startswith('validation/') else SOURCE
            assert digest(source_blob(ref,path))==h,(path,'measured input differs from Git')
        validation=json.loads(files[directory+'validation-summary.json'])
        assert validation['ok'] and validation['source_unchanged'] and validation['named_mutations_expected']==27
        assert validation['all_command_exit_codes_zero'] and not validation['errors']
        commands=json.loads(files[directory+'commands.json'])
        assert len(commands)==10 and all(c['exit_code']==0 for c in commands)
        for c in commands:
            for stream in ('stdout','stderr'):
                original_stream=source_index_path.parent/(c['label']+'.'+stream+'.log')
                assert digest(original_stream.read_bytes())==c[stream+'_sha256']
        mutants=[]
        for family,spec in spec_blobs.items():
            path=directory+f'mutations/{family}/'
            summary=json.loads(files[path+'summary.json'])
            assert summary['baseline']==BASE
            guard=source_blob(SOURCE,spec['guard']).decode('utf-8')
            assert digest(guard.encode())==summary['guard_sha256']
            expected_mutants={m['name']:m for m in spec['mutations']}
            seen=set()
            for rec in summary['records']:
                case=rec['case']; xml=files[path+case+'.xml']; j=junit_summary(xml)
                assert rec['ok'] and rec['errors']==rec['skipped']==0
                assert j['errors']==j['skipped']==0
                if case=='fixed':
                    assert j['passed']==spec['total'] and j['failures']==0 and rec['returncode']==0
                    continue
                if case=='baseline':
                    assert j['failures']==len(spec['baseline_failures']) and sorted(j['failed_names'])==rec['failed_tests']
                    assert set(j['failed_names'])==set(spec['baseline_failures'])
                    assert rec['returncode']==1
                    continue
                mutation=expected_mutants[case]; seen.add(case)
                assert j['testcases']==j['failures']==1 and rec['returncode']==1
                assert j['failed_names']==[mutation['test']]
                failure=ET.fromstring(xml).find('.//testcase/failure')
                assert mutation['assertion'] in (failure.text or '')+(failure.get('message') or '')
                # Reconstruct the mutant from exact source and its named scope.
                candidate={p:source_blob(SOURCE,p).decode('utf-8') for p in spec['sources']}
                for change in mutation['changes']:
                    source=candidate[change['file']]; tree=ast.parse(source); scope=tree
                    if change.get('class'): scope=next(n for n in tree.body if isinstance(n,ast.ClassDef) and n.name==change['class'])
                    method=next(n for n in scope.body if isinstance(n,ast.FunctionDef) and n.name==change['method'])
                    lines=source.splitlines(keepends=True); body=''.join(lines[method.lineno-1:method.end_lineno])
                    assert body.count(change['old'])==1
                    candidate[change['file']]=''.join(lines[:method.lineno-1])+body.replace(change['old'],change['new'],1)+''.join(lines[method.end_lineno:])
                assert {p:digest(s.encode()) for p,s in candidate.items()}==rec['source_sha256']
                mutants.append({'family':family,'case':case,'failure':j['failed_names'][0]})
            assert seen==set(expected_mutants)
        assert len(mutants)==27
        matrices.append({'artifact_root':directory,'inner_original_hashes':raw_hashes,'original_index_count':len(rows),
                         'named_mutants_verified':len(mutants),'mutants':mutants})
    assert sorted(m['original_index_count'] for m in matrices)==[136,136,137]
    index_after=git('ls-files','-s','-z','--',PREFIX)
    assert index_before==index_after,'index changed during independent audit'
    assert git('rev-parse','HEAD').decode().strip()==HEAD
    report={'verdict':'PASS','audited_utc':datetime.now(timezone.utc).isoformat(),'metadata_head':HEAD,
            'measured_source_head':SOURCE,'index_sha256':digest(index_before),'indexed_evidence_files':len(files),
            'manifested_artifacts':len(records),'detached_metadata':sorted(DETACHED),'canonical_blobs':checked,
            'parse_counts':dict(parse_counts),'private_prefix_matches':private,'forbidden_files':forbidden,
            'numeric_json_files_compared':len(numeric_rows),'numeric_bool_leaves_compared':sum(r['numeric_bool_leaves'] for r in numeric_rows),
            'mutable_original_paths_now_different_from_copy_time':mutable_raw_drift,
            'numeric_preservation':numeric_rows,'pr_intake_mappings':mappings,'windows':totals,'windows_gate_ok':False,
            'combined_linux':linux,'benchmark_run':44778606930,'benchmark_matrices':matrices}
    (OUT/'audit-summary.json').write_text(json.dumps(report,indent=2,ensure_ascii=False),encoding='utf-8')
    print(json.dumps({k:v for k,v in report.items() if k not in ('canonical_blobs','numeric_preservation','benchmark_matrices')},indent=2,ensure_ascii=False))


if __name__=='__main__': main()
