"""Build a path-redacted, allowlisted public evidence slice without touching Git.

JSON redaction edits string tokens only (including keys); every other token is
byte-identical. XML is round-tripped and checked structurally, including exact
numeric attributes. Third-party issue bodies are projected to metadata/hashes.
"""
from __future__ import annotations
import argparse
from decimal import Decimal
import hashlib
import json
from pathlib import Path
import re
import sys
import xml.etree.ElementTree as ET

STRING = re.compile(r'"(?:[^"\\]|\\.)*"')
ALLOWED = {'.json', '.jsonl', '.xml', '.log', '.py', '.md'}
DENIED_PARTS = {'__pycache__', '.git', '.pytest_cache', 'pinned-brain-98d6b899',
                'frozen-baseline-124ea43', 'sources', 'lingshu'}


def sha(data):
    return hashlib.sha256(data).hexdigest()


def no_duplicates(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError('duplicate JSON key after redaction: ' + key)
        result[key] = value
    return result


def parse(text):
    return json.loads(text, parse_float=Decimal, object_pairs_hook=no_duplicates)


def encode(value, level=0):
    """Pretty JSON preserving Decimal values exactly for explicit projections."""
    pad, child = '  '*level, '  '*(level+1)
    if value is None:
        return 'null'
    if isinstance(value, bool):
        return 'true' if value else 'false'
    if isinstance(value, (int, Decimal)):
        return str(value)
    if isinstance(value, str):
        return json.dumps(value, ensure_ascii=False)
    if isinstance(value, list):
        return ('[\n' + ',\n'.join(child+encode(v,level+1) for v in value) + '\n'+pad+']') if value else '[]'
    if isinstance(value, dict):
        return ('{\n' + ',\n'.join(child+json.dumps(k,ensure_ascii=False)+': '+encode(v,level+1)
                                    for k,v in value.items()) + '\n'+pad+'}') if value else '{}'
    raise TypeError(type(value).__name__)


def string_tree(value, transform):
    if isinstance(value, str):
        return transform(value)
    if isinstance(value, list):
        return [string_tree(v,transform) for v in value]
    if isinstance(value, dict):
        result = {}
        for key, item in value.items():
            new_key = transform(key)
            if new_key in result:
                raise ValueError('redaction collided JSON keys')
            result[new_key] = string_tree(item,transform)
        return result
    return value


def redactor(source, repo):
    prefixes = [(str(source),'<audit-evidence>'), (str(repo),'<repo>'),
                (str(repo.parent/'lingshu-body-collision-velocity-20261120'),'<no-contact-repo>'),
                (str(repo.parent/'lingshu-audit-round3-20261121'),'<audit-repo>'),
                (str(repo.parent/'lingshu-body-final-validation-20261120-venv'),'<validation-venv>'),
                (str(source.parent),'<round3-evidence>'),
                (str(repo.parent.parent),'<workspace>')]
    variants = []
    for prefix, replacement in prefixes:
        for pattern in {prefix, prefix.replace('\\','/'), prefix.replace('\\','\\\\')}:
            variants.append((pattern,replacement))
    variants.sort(key=lambda pair: len(pair[0]),reverse=True)
    def redact(text):
        for pattern, replacement in variants:
            text = re.sub(re.escape(pattern),lambda _:replacement,text,flags=re.I)
        text = re.sub(r'(?i)(?<![a-z0-9])[a-z]:[\\/]+users[\\/]+[^\\/\s"<>]+',
                      '<user-home>',text)
        text = re.sub(r'(?i)(?<![a-z0-9])([a-z]):[\\/]+',
                      lambda m:'<drive-'+m.group(1).lower()+'>/',text)
        runner_home = '/'.join(('', 'home', 'runner'))
        text = re.sub(re.escape(runner_home)+r'(?:/work)?', '<runner-home>',text,flags=re.I)
        return text
    return redact


def json_redact(text, redact, lines=False):
    def one(original):
        before = parse(original)
        def token(match):
            value = json.loads(match.group())
            public = redact(value)
            return json.dumps(public,ensure_ascii=False) if public != value else match.group()
        public = STRING.sub(token,original)
        assert STRING.sub('"<string>"',original) == STRING.sub('"<string>"',public)
        assert parse(public) == string_tree(before,redact)
        return public
    if lines:
        return ''.join(one(line) if line.strip() else line for line in text.splitlines(keepends=True))
    return one(text)


def xml_snapshot(node):
    return (node.tag, dict(node.attrib), node.text, node.tail, [xml_snapshot(c) for c in node])


def xml_redact(text, redact):
    before = ET.fromstring(text)
    expected = ET.fromstring(text)
    count = 0
    for old, node in zip(before.iter(),expected.iter()):
        for key, value in list(node.attrib.items()):
            if re.fullmatch(r'[-+]?(?:\d+(?:\.\d*)?|\.\d+)(?:[eE][-+]?\d+)?',value):
                assert redact(value) == value
                count += 1
            node.set(key,redact(value))
        node.text = redact(node.text) if node.text is not None else None
        node.tail = redact(node.tail) if node.tail is not None else None
        assert old.tag == node.tag and set(old.attrib) == set(node.attrib)
    public = ET.tostring(expected,encoding='unicode',xml_declaration=True)
    assert xml_snapshot(ET.fromstring(public)) == xml_snapshot(expected)
    return public, count


def self_test():
    drive = chr(69)+':'+chr(92)
    redact = lambda value:value.replace(drive+'private','<private>')
    original = '{"'+json.dumps(drive+'private'+chr(92)+'key')[1:-1]+'":1.2300e-20,"array":[12345678901234567890,-0.0,true,null,"'+json.dumps(drive+'private'+chr(92)+'value')[1:-1]+'"]}'
    public = json_redact(original,redact)
    assert '1.2300e-20' in public and '12345678901234567890' in public and '-0.0' in public
    assert list(parse(public))[0].startswith('<private>')
    xml = '<testsuite tests="1" failures="1" time="0.123000"><testcase file="'+drive+'private'+chr(92)+'a.py"><failure>delta=1.234567890123 '+drive+'private'+chr(92)+'a.py</failure></testcase></testsuite>'
    result, count = xml_redact(xml,redact)
    assert '0.123000' in result and '1.234567890123' in result and count == 3
    assert parse(encode(parse(original))) == parse(original)
    return {'json_keys_and_values':True,'nonstring_tokens_byte_identical':True,
            'big_integer_and_float_lexemes':True,'xml_numeric_attributes_and_structure':True,
            'projection_decimal_roundtrip':True}


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source',type=Path,required=True)
    parser.add_argument('--repo',type=Path,required=True)
    parser.add_argument('--output',type=Path,required=True)
    parser.add_argument('--include-full-gate',action='store_true')
    args=parser.parse_args()
    source, repo, output=args.source.resolve(),args.repo.resolve(),args.output.resolve()
    assert source.is_dir() and repo.is_dir() and output != source and output != repo
    output.mkdir(parents=True,exist_ok=True)
    redact=redactor(source,repo)
    records=[]
    targets=set()
    def put(path, relative, label, projection=None, note=None):
        relative=Path(relative)
        assert not relative.is_absolute() and '..' not in relative.parts
        assert relative.suffix in ALLOWED
        assert not any(part in DENIED_PARTS for part in relative.parts)
        dest=(output/relative).resolve(); assert dest.is_relative_to(output)
        assert str(relative).replace('\\','/') not in targets
        targets.add(str(relative).replace('\\','/'))
        raw=path.read_bytes(); before_stat=path.stat()
        text=raw.decode('utf-8-sig')
        original_text=text
        projected=False
        if projection is not None:
            expected=projection(parse(text)); text=encode(expected)+'\n'
            assert parse(text)==expected
            projected=True
        checks={}
        if relative.suffix in ('.json','.jsonl'):
            public=json_redact(text,redact,lines=relative.suffix=='.jsonl')
            checks={'json_keys_values_checked':True,'nonstring_tokens_byte_identical':True,
                    'projection_numeric_values_preserved':True if projected else None}
        elif relative.suffix=='.xml':
            public,numeric_count=xml_redact(text,redact)
            checks={'xml_structure_and_text_checked':True,'exact_numeric_attributes_checked':numeric_count}
        else:
            public=redact(text)
        payload=public.encode('utf8')
        dest.parent.mkdir(parents=True,exist_ok=True);dest.write_bytes(payload)
        assert dest.read_bytes()==payload
        after_stat=path.stat();assert (before_stat.st_size,before_stat.st_mtime_ns)==(after_stat.st_size,after_stat.st_mtime_ns)
        assert sha(path.read_bytes())==sha(raw),'source changed while copying'
        records.append({'source':label,'public':relative.as_posix(),'status':note or 'final',
                        'raw_sha256':sha(raw),'raw_bytes':len(raw),
                        'projected_input_sha256':sha(text.encode('utf8')) if projected else None,
                        'public_sha256':sha(payload),'public_bytes':len(payload),
                        'projection':projected,'checks':checks})
    def local(name,dest,status='final',projection=None):
        path=(source/name).resolve();assert path.is_relative_to(source)
        assert path.is_file(),name
        put(path,dest,name,projection,status)
    final_names=['command-final-adjacent.log','command-final-adjacent.xml','command-fixed-actual-endpoint.log',
                 'command-fixed-actual-endpoint.xml','command-final-manifest.json','command-final-time-core.json',
                 'command-final-mutations-driver.log','command-benchmark-actual-endpoint-memory.log',
                 'command-benchmark-actual-endpoint-oracle.log','command-benchmark-actual-endpoint-timing.log']
    for name in final_names: local(name,'final/'+name)
    for name in ['command-delivery-metadata.json','command-doc-only-provenance.json',
                 'command-source-freeze.json','command-post-rebase-source-hashes.json',
                 'command-pre-rebase-source-hashes.json','command-brain-setup.json','command-brain-setup.log']:
        local(name,'provenance/'+name,'local-run/provenance')
    for name in ['command-collision-interaction.json','probe_command_collision_interaction.py']:
        local(name,'final/interaction/'+name)
    for name in ['probe_seven_layer_command_resume.json','probe_seven_layer_command_resume.py',
                 'neighbor-action-contract.log','neighbor-action-contract.xml']:
        local(name,'audit/'+name,'baseline audit before implementation')
    local('probe_state_anchors.json','audit/probe-state-anchors-command-only.json',
          'command-only projection; separate environment audit withheld',
          lambda d:{'head':d['head'],'commands':d['commands'],'summary':{k:v for k,v in d['summary'].items() if k.startswith('commands')}})
    for folder,dest,status in [('command-final-mutations','final/mutations','final'),
                               ('command-mutations','intermediate/mutations-first','INTERMEDIATE: rounded public velocity assumption'),
                               ('command-mutations-r2','intermediate/mutations-second','INTERMEDIATE: rounded public velocity assumption')]:
        for path in sorted((source/folder).iterdir()):
            if path.is_file() and path.suffix in ('.json','.xml','.log'):
                local(str(path.relative_to(source)),dest+'/'+path.name,status)
    for folder,dest,status in [('command-benchmark-actual-endpoint','final/benchmark','final actual endpoint displacement'),
                               ('command-benchmark','intermediate/benchmark','INTERMEDIATE: rounded public velocity assumption')]:
        for name in ['oracle.json','oracle-cases.jsonl','timing.json','memory.json']:
            local(folder+'/'+name,dest+'/'+name,status)
    local('command-benchmark-actual-endpoint/benchmark-driver.py','final/benchmark/benchmark-driver.py')
    for name in ['command-adjacent.log','command-adjacent.xml','command-baseline.log','command-baseline.xml',
                 'command-fixed.log','command-fixed.xml','command-manifest.json','command-time-core.json',
                 'command-mutations-driver.log','command-mutations-r2-driver.log',
                 'command-benchmark-memory.log','command-benchmark-oracle.log','command-benchmark-timing.log',
                 'command-physics-broad.log','command-physics-broad.xml','command-continuous-position-boundary.json',
                 'INTERMEDIATE_EVIDENCE.md']:
        local(name,'intermediate/'+name,'INTERMEDIATE: superseded or pre-final proof')
    for name in ['README.md','bench/bench_dynamics_command_reanchor.py','tests/test_dynamics_command_reanchor.py',
                 'tests/fixtures/dynamics_command_reanchor_mutations.json']:
        local('command-intermediate-public-velocity/'+name,'intermediate/public-velocity-attempt/'+name,
              'INTERMEDIATE: rounded public velocity assumption')
    for name in ['tests/test_dynamics_command_reanchor.py','tests/fixtures/dynamics_command_reanchor_mutations.json',
                 'bench/bench_dynamics_command_reanchor.py','docs/testing/dynamics-command-reanchor-20261121/README.md',
                 'docs/testing/dynamics-command-reanchor-20261121/validation-summary.json']:
        put(repo/name,'final/repository/'+name,'<repo>/'+name)
    def report_projection(d):
        return {'searches':d['searches'],'closest_comments':[
            {'repository':r['repository'],'number':r['number'],'comments':r['comments'],
             'relevant':[{'url':c['url'],'body_sha256_utf8':sha(c['body'].encode('utf8'))} for c in r['relevant']]}
            for r in d['closest_comments']]}
    local('dedup-state-anchor-report.json','audit/dedup/report-metadata.json',
          'metadata projection; all third-party comment bodies withheld',report_projection)
    for name in ['lingshu-anchor-matches.json','bounty-anchor-matches.json']:
        local(name,'audit/dedup/'+name,'selected issue/PR metadata only')
    for path in sorted((source/'dedup-search').glob('*.json')):
        def search_projection(d):
            return {k:([{key:value for key,value in item.items() if key in
                        {'number','title','html_url','state','created_at','updated_at','closed_at','comments','repository_url'}}
                       for item in value] if k=='items' else value)
                    for k,value in d.items() if k in {'total_count','incomplete_results','search_type','items'}}
        local(str(path.relative_to(source)),'audit/dedup/search/'+path.name,
              'search metadata projection; issue bodies/users/payloads withheld',search_projection)
    for path in sorted((source/'dedup-comments').glob('*.json')):
        def comment_projection(d):
            def flatten(items):
                for item in items:
                    if isinstance(item,list):
                        yield from flatten(item)
                    else:
                        assert isinstance(item,dict)
                        yield item
            comments=list(flatten(d))
            return [{**{k:v for k,v in c.items() if k in {'id','node_id','html_url','issue_url','created_at','updated_at'}},
                     'body_sha256_utf8':sha(c.get('body','').encode('utf8'))} for c in comments]
        local(str(path.relative_to(source)),'audit/dedup/comments/'+path.name,
              'comment metadata projection; full bodies/users withheld',comment_projection)
    if args.include_full_gate:
        summary=source/'command-full-gate/summary.json';assert summary.is_file()
        gate=parse(summary.read_text(encoding='utf-8-sig'))
        assert 'all_commands_exit_zero' in gate and len(gate['records']) == gate['scripts']+3
        assert gate['records'][-1]['name']=='time-core' and 'pytest' in gate
        for path in sorted((source/'command-full-gate').iterdir()):
            if path.is_file() and path.suffix in ('.log','.json','.xml'):
                local(str(path.relative_to(source)),'final/full-gate/'+path.name,'completed full Windows gate')
        local('command-full-gate-driver.log','final/full-gate-driver.log','completed full Windows gate')
        for name in ['command-full-gate-provenance.json','command-final-seal.json']:
            if (source/name).exists(): local(name,'provenance/'+name,'completed full-run seal')
        for name in ['command-symlink-capability.json','probe_symlink_capability.py']:
            if (source/name).exists(): local(name,'final/full-gate/'+name,'capability-only diagnosis; original failure retained')
    local('command_full_gate.py','helpers/command_full_gate.py','self-authored validation driver')
    put(Path(__file__).resolve(),'helpers/prepare_public_world_slice.py','self-authored public-slice helper')
    tests=self_test()
    info={'schema':1,'source':'path-redacted allowlist from audit-world','full_gate_included':args.include_full_gate,
          'head':'bd208a379e44497e9f35fdc145838abb19e6d313','production_sha256_lf':'984d8abeaaa5a4b9d50e6d604758ac128d120f6b3bd56289b8b2a665a7bd1046',
          'self_tests':tests,'file_count':len(records),'entries':records,
          'excluded':['brain clone','frozen baseline tree','all zip archives','DB/pyc/cache',
                      'complete third-party production snapshots','aggregate issue snapshots',
                      'all third-party issue/comment bodies','separate unadjudicated environment-change audit',
                      'active full-gate outputs unless explicitly included after completion'],
          'third_party_snapshot_inventory':[{'name':name,'raw_sha256':sha((source/name).read_bytes()),
                                             'raw_bytes':(source/name).stat().st_size,'included':False}
                                            for name in ['lingshu-all-issues.json','bounty-all-issues.json']]}
    (output/'public-index.json').write_text(encode(info)+'\n',encoding='utf8',newline='\n')
    readme='''# World command reanchor public evidence slice

Final production head: `bd208a379e44497e9f35fdc145838abb19e6d313` (PR #1482).
The final implementation uses unrounded endpoint displacement for directional
commands and zero physical velocity for explicit stay. `intermediate/` is the
superseded attempt that used the rounded public velocity. Its original oracle
shared that assumption and is not final correctness proof.

`public-index.json` binds every retained file to its original and public byte
length/SHA256, states projections, and records verification checks. It does not
index itself or this explanatory README to avoid self-reference. JSON redaction
changes string tokens only, including dictionary keys, and checks identical
non-string tokens. Explicit metadata projections preserve retained numeric
values exactly with Decimal parsing. XML structure, text after path redaction,
and numeric attributes are verified after serialization.

Absolute paths become `<repo>`, `<audit-evidence>`, `<validation-venv>`,
`<no-contact-repo>`, `<user-home>` and related placeholders. Helpers are retained
for audit and can be rerun with explicit source/repository/output arguments;
standalone probe path placeholders must be configured for the target checkout.
No brain/baseline source tree, archive, database, cache, complete third-party
production snapshot, aggregate issue dump, or third-party issue/comment body is
included. Dedup evidence contains selected metadata, URLs, counts and body hashes.
The separate environment-change hypothesis is withheld from this command fix.

The full Windows gate is included only after its process has ended. Its code
input was frozen at 6d1048f6; the subsequent bd208a commit added two documentation
files. The original end-of-run head and any source-drift observations remain
unchanged; this slice does not relabel an entire-tree change as identical source.
The original Windows run has one failed pre-existing symlink-capability
assertion: this Windows host can create a real symlink, while that guard assumes
success implies POSIX. The unchanged test hash and independent capability probe
are retained. Original exit codes and failure/skip counts are not rewritten.
'''
    (output/'README.md').write_text(readme,encoding='utf8',newline='\n')
    expected=targets|{'README.md','public-index.json'}
    actual={p.relative_to(output).as_posix() for p in output.rglob('*') if p.is_file()}
    assert actual==expected,(actual-expected,expected-actual)
    leaks=[]
    for path in output.rglob('*'):
        if not path.is_file():continue
        text=path.read_text(encoding='utf8')
        leak_pattern=r'(?i)(?<![a-z0-9])[a-z]:[\\/]+|[\\/]+users[\\/]+[0-9]+|'+re.escape('/'.join(('', 'home', 'runner')))
        if re.search(leak_pattern,text):
            leaks.append(path.relative_to(output).as_posix())
    assert not leaks,leaks
    for record in records:
        payload=(output/record['public']).read_bytes()
        assert sha(payload)==record['public_sha256'] and len(payload)==record['public_bytes']
    print(json.dumps({'files':len(records),'full_gate_included':args.include_full_gate,
                      'bytes':sum(r['public_bytes'] for r in records),'self_tests':tests,
                      'path_leaks':leaks,'public_index_sha256':sha((output/'public-index.json').read_bytes())}))


if __name__=='__main__':
    main()
