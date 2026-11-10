"""Build an isolated FIN01 revision from frozen public EIA archive files.

No browser automation and no model or platform submission.
"""
from __future__ import annotations

import csv
import hashlib
import io
import json
import re
import shutil
import statistics
import zipfile
from collections import Counter, defaultdict
from datetime import date, datetime, timedelta
from decimal import Decimal
from pathlib import Path
from zoneinfo import ZoneInfo

ROOT = Path(__file__).resolve().parents[2]
RAW = ROOT / 'runs/fin01-v2/source-raw'
PACK = ROOT / 'packs/fin01-v2'
MAT = PACK / 'materials'
GT = PACK / 'author/ground-truth'
NY, CN = ZoneInfo('America/New_York'), ZoneInfo('Asia/Shanghai')
HOLIDAYS = {'2025-09-04', '2025-10-16', '2025-11-13'}


def write_csv(path, rows):
    rows = list(rows)
    with path.open('w', newline='', encoding='utf-8-sig') as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def read_raw(path):
    # The legacy EIA CSVs use Windows-1252 en dashes and a DOS EOF marker.
    return list(csv.reader(io.StringIO(path.read_bytes().decode('cp1252').rstrip('\x1a'))))


def numeric(value):
    return Decimal(value.replace(',', ''))


def build():
    for p in [MAT / 'raw', GT]:
        p.mkdir(parents=True, exist_ok=True)
    fetches = json.loads((RAW / 'FETCH-MANIFEST.json').read_text())
    assert len(fetches) == 61 and not any('error' in r for r in fetches)
    manifest = []
    for r in fetches:
        src, dst = RAW / r['file'], MAT / 'raw' / r['file']
        shutil.copyfile(src, dst)
        assert hashlib.sha256(dst.read_bytes()).hexdigest() == r['sha256']
        manifest.append({
            'file': 'raw/' + r['file'], 'format': src.suffix[1:],
            'source_url': r['url'],
            'version_or_date': r['file'][:10].replace('_', '-') if r['file'][0].isdigit() else 'snapshot 2026-11-10',
            'fetched_at': r['fetched_at'],
            'data_rows': sum(bool(row) and row[0] != 'STUB_1' for row in read_raw(src)) if src.suffix == '.csv' else 'not a data table',
            'bytes': r['bytes'], 'sha256': r['sha256'],
        })
    write_csv(MAT / '05_来源清单.csv', manifest)
    releases = sorted(p.name[:10] for p in RAW.glob('*_release.html'))
    candidates, field_defs, release_rows = [], {}, []

    def add(rel, table, row_idx, col_idx, key, meaning, region, unit, period='week', priority=1):
        rows = read_raw(RAW / f'{rel}_table{table}.csv')
        row = rows[row_idx]
        header_row = 20 if table == 1 and row_idx >= 21 else 0
        obs = datetime.strptime(rows[header_row][col_idx], '%m/%d/%y').date().isoformat()
        raw_val = row[col_idx]
        val = numeric(raw_val)
        normalized = val * 1000 if unit == 'million_barrels' else val
        canonical_unit = 'thousand_barrels' if unit == 'million_barrels' else unit
        field_defs[key] = {'field_id': key, 'meaning': meaning, 'region': region,
                           'unit': canonical_unit, 'period': period}
        feed = f'T{table}'
        record_id = f'{rel}:{feed}:r{row_idx+1}:c{col_idx+1}'
        candidates.append({
            'record_id': record_id, 'feed': feed, 'release_date': rel.replace('_', '-'),
            'field_id': key, 'observation_week': obs, 'raw_value': str(val),
            'raw_unit': unit, 'normalized_value': str(normalized),
            'canonical_unit': canonical_unit, 'period': period, 'priority': priority,
            'file': f'raw/{rel}_table{table}.csv', 'row': row_idx + 1, 'column': col_idx + 1,
        })

    for rel in releases:
        rel_date = rel.replace('_', '-')
        hh, mm = (12, 0) if rel_date in HOLIDAYS else (10, 30)
        pub = datetime.fromisoformat(rel_date).replace(hour=hh, minute=mm, tzinfo=NY)
        release_rows.append({'release_date': rel_date, 'published_ny': pub.isoformat(),
                             'published_cn': pub.astimezone(CN).isoformat()})
        t1 = read_raw(RAW / f'{rel}_table1.csv')
        stock = [(1, 'crude_total', '原油总库存（含SPR）'),
                 (2, 'crude_commercial', '商业原油库存（不含SPR）'),
                 (3, 'spr', '战略石油储备库存'), (4, 'gasoline', '汽车汽油总库存'),
                 (10, 'distillate', '馏分燃料油库存')]
        for ridx, field, name in stock:
            for c in [1, 2]:
                add(rel, 1, ridx, c, 'stock_' + field + '_US', name, 'US', 'million_barrels', priority=2)
        flow_ids = {
            1: ('production', '国内原油产量'), 4: ('transfers', '转入原油供给'),
            7: ('net_imports', '原油净进口（含SPR）'), 8: ('imports', '原油进口'),
            10: ('imports_spr', 'SPR原油进口'), 12: ('exports', '原油出口'),
            13: ('stock_change_total', '原油总库存变化（日均）'),
            14: ('stock_change_commercial', '商业原油库存变化（日均）'),
            15: ('stock_change_spr', 'SPR库存变化（日均）'),
            16: ('adjustment', '原油供给调整项'), 17: ('crude_inputs', '炼厂原油投入'),
            31: ('gasoline_demand', '汽车汽油产品供应量'),
            33: ('distillate_demand', '馏分燃料油产品供应量'),
        }
        for ridx, row in enumerate(t1):
            if len(row) < 3:
                continue
            hit = re.match(r'\((\d+)\)', row[1])
            if not hit or int(hit[1]) not in flow_ids:
                continue
            n = int(hit[1])
            # Table 1 has a second '(33) Total' in an unrelated section.
            if n == 33 and not row[1].endswith('Distillate Fuel Oil'):
                continue
            field, name = flow_ids[n]
            for c in [2, 3]:
                add(rel, 1, ridx, c, field + '_US', name, 'US', 'thousand_barrels_per_day')
            if n in [17, 31, 33]:
                add(rel, 1, ridx, 7, field + '_4w_US', name + '（四周日均）', 'US',
                    'thousand_barrels_per_day', period='4week_average')
        blocks = [('crude_inputs', '炼厂原油投入'), ('gross_inputs', '炼厂总投入'),
                  ('capacity', '可运行炼油产能'), ('utilization', '炼厂利用率')]
        for b, (field, name) in enumerate(blocks):
            for j in range(6):
                region = 'US' if j == 0 else f'PADD{j}'
                for c in [2, 3]:
                    add(rel, 2, 1 + b*6 + j, c, f'{field}_{region}', name, region,
                        'percent' if field == 'utilization' else 'thousand_barrels_per_day', priority=2 if field == 'crude_inputs' and region == 'US' else 1)
        stocks4 = [(1, 'crude_total', 'US'), (2, 'crude_commercial', 'US'),
                   (3, 'crude_commercial', 'PADD1'), (4, 'crude_commercial', 'PADD2'),
                   (5, 'crude_commercial', 'CUSHING'), (6, 'crude_commercial', 'PADD3'),
                   (7, 'crude_commercial', 'PADD4'), (8, 'crude_commercial', 'PADD5'),
                   (9, 'crude_commercial', 'ALASKA_TRANSIT'), (10, 'spr', 'US'),
                   (11, 'gasoline', 'US'), (17, 'distillate', 'US')]
        for ridx, field, region in stocks4:
            for c in [1, 2]:
                add(rel, 4, ridx, c, f'stock_{field}_{region}', f'{field}库存', region, 'million_barrels')

    # Scenario assumptions are deliberately separated from real public data.
    receipt_lag = {'T1': 10, 'T2': 25, 'T4': 55}
    publication = {r['release_date']: datetime.fromisoformat(r['published_ny']) for r in release_rows}
    for r in candidates:
        r['available_base'] = (publication[r['release_date']] + timedelta(minutes=receipt_lag[r['feed']])).astimezone(CN).isoformat()
        r['available_stress'] = (datetime.fromisoformat(r['available_base']) + timedelta(hours=24 if r['feed'] == 'T2' else 0)).isoformat()
    assert len({r['record_id'] for r in candidates}) == len(candidates)
    write_csv(GT / 'all_candidates.csv', candidates)
    fields = sorted(field_defs.values(), key=lambda x: x['field_id'])
    write_csv(MAT / '02_字段需求.csv', fields)
    write_csv(GT / 'release_calendar.csv', release_rows)

    cutoffs = []
    for i, r in enumerate(release_rows, 1):
        pub = datetime.fromisoformat(r['published_cn'])
        for suffix, minutes in [('A', -15), ('B', 20), ('C', 40), ('D', 70)]:
            cutoffs.append({'case_id': f'W{i:02d}{suffix}', 'cutoff_cn': (pub+timedelta(minutes=minutes)).isoformat()})
    write_csv(MAT / '03_决策时点.csv', cutoffs)
    entities = [
        {'region':'US','parent':'','aggregation':'全美；不能与分区再次相加'},
        *[{'region':f'PADD{i}','parent':'US','aggregation':'五个PADD组成全美，不含额外子集加总'} for i in range(1,6)],
        {'region':'CUSHING','parent':'PADD2','aggregation':'PADD2子集；不得与PADD2重复相加'},
        {'region':'ALASKA_TRANSIT','parent':'','aggregation':'单列观察；本包不证明其归属单一PADD，不作为额外PADD加入全美求和'},
    ]
    write_csv(MAT / '06_区域映射.csv', entities)

    by_field = defaultdict(list)
    for r in candidates:
        by_field[r['field_id']].append(r)
    panel, derived, source_coverage = [], [], []
    for scenario in ['base', 'stress']:
        for case in cutoffs:
            cutoff = datetime.fromisoformat(case['cutoff_cn'])
            chosen = {}
            for field in fields:
                fid = field['field_id']
                valid = [r for r in by_field[fid] if datetime.fromisoformat(r['available_'+scenario]) <= cutoff]
                # Freshest observation, best source for that observation, freshest archive issue.
                r = max(valid, key=lambda x: (x['observation_week'], -x['priority'], x['release_date'])) if valid else None
                if r:
                    chosen[fid] = r
                panel.append({'scenario':scenario, **case, 'field_id':fid,
                              'observation_week':r['observation_week'] if r else '',
                              'value':r['normalized_value'] if r else '',
                              'unit':field['unit'], 'state':'AVAILABLE' if r else 'NOT_OBSERVED',
                              'record_id':r['record_id'] if r else ''})
            # Downstream decision must use the freshest common observation week.
            needed = ['stock_crude_commercial_US','stock_gasoline_US','stock_distillate_US',
                      'crude_inputs_4w_US','gasoline_demand_4w_US','distillate_demand_4w_US',
                      'gross_inputs_US','capacity_US']
            available = {fid: [r for r in by_field[fid] if datetime.fromisoformat(r['available_'+scenario]) <= cutoff] for fid in needed}
            common = set.intersection(*(set(r['observation_week'] for r in rows) for rows in available.values()))
            if not common:
                derived.append({'scenario':scenario, **case,'observation_week':'','crude_days':'','gasoline_days':'','distillate_days':'','utilization_percent':'','decision':'待补证','evidence':''})
                continue
            week = max(common)
            selected = {}
            for fid, rows in available.items():
                selected[fid] = max([r for r in rows if r['observation_week']==week],key=lambda x:(-x['priority'],x['release_date']))
            v = {fid:numeric(r['normalized_value']) for fid,r in selected.items()}
            oil = v['stock_crude_commercial_US']/v['crude_inputs_4w_US']
            gas = v['stock_gasoline_US']/v['gasoline_demand_4w_US']
            dist = v['stock_distillate_US']/v['distillate_demand_4w_US']
            util = 100*v['gross_inputs_US']/v['capacity_US']
            decision = '限制发布' if gas < 24 or dist < 28 or util < 90 else '可发布'
            derived.append({'scenario':scenario, **case,'observation_week':week,
                            'crude_days':f'{oil:.6f}','gasoline_days':f'{gas:.6f}',
                            'distillate_days':f'{dist:.6f}','utilization_percent':f'{util:.6f}',
                            'decision':decision,'evidence':';'.join(selected[fid]['record_id'] for fid in needed)})
    write_csv(GT / 'pit_panel.csv', panel)
    write_csv(GT / 'decision_panel.csv', derived)

    controls = []
    for rel in releases:
        cur = [r for r in candidates if r['release_date']==rel.replace('_','-')]
        week = max(r['observation_week'] for r in cur)
        vals = {}
        for r in cur:
            if r['observation_week']==week and (r['field_id'] not in vals or r['priority']<vals[r['field_id']]['priority']):
                vals[r['field_id']] = r
        def val(fid): return numeric(vals[fid]['normalized_value'])
        checks = [
            ('CRUDE_COMPONENTS', val('stock_crude_total_US')-val('stock_crude_commercial_US')-val('stock_spr_US'), Decimal('2')),
            ('REGIONAL_COMMERCIAL',sum(val(f'stock_crude_commercial_PADD{i}') for i in range(1,6))-val('stock_crude_commercial_US'),Decimal('3')),
            ('REGIONAL_CRUDE_INPUTS',sum(val(f'crude_inputs_PADD{i}') for i in range(1,6))-val('crude_inputs_US'),Decimal('3')),
            ('REGIONAL_GROSS_INPUTS',sum(val(f'gross_inputs_PADD{i}') for i in range(1,6))-val('gross_inputs_US'),Decimal('3')),
            ('REGIONAL_CAPACITY',sum(val(f'capacity_PADD{i}') for i in range(1,6))-val('capacity_US'),Decimal('3')),
            ('UTILIZATION',100*val('gross_inputs_US')/val('capacity_US')-val('utilization_US'),Decimal('0.06')),
            ('CRUDE_BALANCE',val('production_US')+val('transfers_US')+val('net_imports_US')+val('adjustment_US')-val('stock_change_total_US')-val('crude_inputs_US'),Decimal('3')),
        ]
        t1 = read_raw(RAW/f'{rel}_table1.csv')
        for stock,flow,ridx in [('crude_total','total',1),('crude_commercial','commercial',2),('spr','spr',3)]:
            delta = (numeric(t1[ridx][1])-numeric(t1[ridx][2]))*1000/7
            checks.append((f'STOCK_FLOW_{stock}',delta-val(f'stock_change_{flow}_US'),Decimal('0.7')))
        for name,residual,tolerance in checks:
            controls.append({'release_date':rel.replace('_','-'),'observation_week':week,'check_id':name,
                             'residual':f'{residual:.9f}','tolerance':str(tolerance),'verdict':'PASS' if abs(residual)<=tolerance else 'FAIL'})
    write_csv(GT / 'controls.csv', controls)
    dup = defaultdict(list)
    for r in candidates:
        dup[(r['field_id'],r['observation_week'],r['feed'])].append(r)
    revisions=[]
    for (fid,week,feed), rows in dup.items():
        rows.sort(key=lambda x:x['release_date'])
        for before,after in zip(rows,rows[1:]):
            if before['normalized_value'] != after['normalized_value']:
                revisions.append({'field_id':fid,'observation_week':week,'feed':feed,
                                  'earlier_record':before['record_id'],'later_record':after['record_id'],
                                  'earlier_value':before['normalized_value'],'later_value':after['normalized_value']})
    if revisions:
        write_csv(GT / 'cross_issue_changes.csv', revisions)
    counts={'archive_issues':len(releases),'raw_files':len(manifest),'raw_csv_data_rows':sum(r['data_rows'] for r in manifest if isinstance(r['data_rows'],int)),
            'canonical_fields':len(fields),'candidate_values':len(candidates),'decision_cutoffs':len(cutoffs),
            'pit_panel_rows':len(panel),'decision_rows':len(derived),'control_rows':len(controls),
            'control_failures':[r for r in controls if r['verdict']=='FAIL'],
            'cross_issue_changed_values':len(revisions),'decision_distribution':dict(Counter(r['decision'] for r in derived)),
            'unavailable_panel_rows':sum(r['state']!='AVAILABLE' for r in panel)}
    (GT/'summary.json').write_text(json.dumps(counts,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps(counts,ensure_ascii=False,indent=2))


if __name__ == '__main__':
    build()
