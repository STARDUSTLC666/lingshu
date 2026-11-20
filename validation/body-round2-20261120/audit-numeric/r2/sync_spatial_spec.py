from pathlib import Path
import json
import xml.etree.ElementTree as ET

ROOT=Path(r'[workspace]/lingshu/work\lingshu-body-spatial-partition-20261120')
path=ROOT/'tests/fixtures/spatial_detect_complete_partition_mutations.json'
old=json.loads(path.read_text(encoding='utf-8'))
mutants=[]
for item in old['mutations'][:4]:
    item=dict(item)
    previous=item.pop('old')
    replacement=item.pop('new')
    item['changes']=[{'file':'lingshu/nn/hex_text.py','method':'spatial_detect',
                      'old':previous,'new':replacement}]
    mutants.append(item)
mutants.extend([
    {'name':'allow_empty_dominant_region','test':'test_dark_tiny_lattice_does_not_classify_empty_quadrants[1-1]',
     'assertion':'nonempty dominant region disappeared',
     'changes':[{'file':'lingshu/nn/hex_text.py','method':'spatial_detect',
                 'old':'keep_q = {max(nonempty, key=lambda q: shares[q])}',
                 'new':'keep_q = {int(shares.argmax())}'}]},
    {'name':'fixed_one_ninth_area_baseline','test':'test_uniform_real_network_does_not_mistake_area_for_extra_evidence[transparent-1.0-5-5]',
     'assertion':'uniform field produced extra detections from unequal quadrant areas',
     'changes':[{'file':'lingshu/nn/hex_text.py','method':'spatial_detect',
                 'old':'if shares[q] > area_shares[q] * exist_mult:',
                 'new':'if shares[q] > (1.0 / 9.0) * exist_mult:'}]}
])
tests=ET.parse(Path(__file__).parent/'baseline.xml').findall('.//testcase')
report={'guard':old['guard'],'total':len(tests),'sources':old['sources'],
        'baseline_failures':sorted(t.get('name') for t in tests if t.find('failure') is not None),
        'mutations':mutants}
path.write_text(json.dumps(report,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
print(json.dumps({'total':report['total'],'failures':len(report['baseline_failures']),
                  'mutations':len(mutants)},indent=2))
