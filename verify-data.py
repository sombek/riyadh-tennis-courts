"""Regression checks against the preserved original venue records."""
import json, re
from pathlib import Path
root=Path(__file__).resolve().parent
old=json.loads((root/'source-records.json').read_text())
new=json.loads((root/'courts.json').read_text())
assert len(old)==len(new)==15
assert sum(bool(c['prices']) for c in new)==13
assert len({c['id'] for c in new})==15
for before,after in zip(old,new):
    assert re.fullmatch(r'[a-z0-9-]+',after['id'])
    assert before['name']==after['name']
    assert (before['area'] or None)==after['locationText']
    assert before['map']==after['map']['url']
    assert set(after)==set(new[0])
    if before['price'] is not None:
        assert before['price']==after['prices'][0]['amount']
    for p in before.get('pricing',[]):
        assert any(p['amount']==q['amount'] for q in after['prices'])
    for field in ['booking','androidApp','iosApp']:
        if before.get(field):assert before[field] in [l['url'] for l in after['booking']['links']]
    for field in ['phone','callPhone']:
        if before.get(field):assert before[field] in [c['raw'] for c in after['booking']['contacts']]
    assert after['provenance']['verifiedAt'] is None
by_id={c['id']:c for c in new}
assert by_id['al-yamamah']['booking']['contacts'][0]['e164'] is None
assert by_id['tennis-home']['prices'][0]['durationMinutes']==120
assert sorted(p['amount'] for p in by_id['najd']['prices'])==[99,150]
assert sum('duration_unspecified' in c['issues'] for c in new)==5
bundle=(root/'courts-data.js').read_text().split('window.COURTS_DATA = ',1)[1].rstrip().removesuffix(';')
assert json.loads(bundle)==new
print('PASS: all 15 venues, source prices, tier amounts, locations, contact values, and URLs preserved; data bundle matches canonical JSON.')
