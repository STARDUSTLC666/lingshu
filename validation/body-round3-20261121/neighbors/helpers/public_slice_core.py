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


