# RETIRED 2026-11-25: the draft went live as operational/Calperum.yml; edit
# that directly from now on. Do NOT rerun this script: it reads
# operational/Calperum.yml as the new-era source, so running it now would
# stitch the already-stitched config again. Kept as the record of how the
# stitched config was built.
#
# Generates the stitched Calperum draft: legacy CR3000 era (legacy/Calperum.yml,
# 2021-09-09 15:30 -> 2024-12-16 08:30) + TERNflux CR1000X era
# (operational/Calperum.yml, from 2024-12-17 15:30).
# Usage: python make_draft.py /opt/TERN_EP/site_configs/drafts/Calperum/Calperum.yml
# (also writes Calperum_review.csv beside it). Once the draft goes live this
# script must be RETIRED (it reads operational/Calperum.yml as the new-era source).
#
# Decisions (user, 2026-11-25):
# - Old IRGA relabelled LI-7500RS (it logs signal strength 0-100, which the
#   original LI-7500 doesn't), so both eras are the same model.
# - Upper WindSentry stays at 8 m in both eras as in the legacy config;
#   the old raw names say '@7m': PROVISIONAL, follow up with the operator.
# - Soil logger (Calperum_soil_slow_soil2): master + .backup share columns
#   (except Vbat), already continuous; left untouched.
import copy, csv, sys
from collections import Counter
import yaml

BASE = '/opt/TERN_EP/site_configs'
NEW = yaml.safe_load(open(f'{BASE}/operational/Calperum.yml'))
OLD = yaml.safe_load(open(f'{BASE}/legacy/Calperum.yml'))
OUT = sys.argv[1]
END = '2024-12-16 08:30'
BEGIN = '2024-12-17 15:30'
SOIL = 'Calperum_soil_slow_soil2'
IRGA = 'LI-COR LI-7500RS'
CSAT = 'Campbell Scientific CSAT3B'

# Old variance variables feed the new standard-deviation ones.
VR = {'Tv_SONIC_Vr': 'Tv_SONIC_Sd', 'Ux_SONIC_Vr': 'Ux_SONIC_Sd',
      'Uy_SONIC_Vr': 'Uy_SONIC_Sd', 'Uz_SONIC_Vr': 'Uz_SONIC_Sd',
      'AH_IRGA_Vr': 'AH_IRGA_Sd', 'CO2c_IRGA_Vr': 'CO2c_IRGA_Sd'}
# Old inputs present in the raw files but missing from the legacy config.
EXTRA_OLD = {
    'Fm': {'name': 'Fm_Avg', 'instrument': CSAT, 'units': 'kg/m/s^2', 'file': 'Calperum_EC_slow_flux'},
    'Wd_SONIC_Sd': {'name': 'WD_CSAT_Sd', 'instrument': CSAT, 'units': 'degrees', 'file': 'Calperum_EC_slow_met'},
}
DROP_OLD = {'Vbat_b': 'second (soil) logger battery; removed network-wide (see network-variable-standardization)'}
NOTES = {
    'Ws_8m_Av': ('provisional', "old raw column 'Wind_speed_m/s@7m': PROVISIONAL 8 m height kept as in the legacy config (user 2026-11-25); confirm with operator"),
    'Wd_8m_Av': ('provisional', "old raw column 'Wind_Dir_mean@7m': PROVISIONAL 8 m height kept as in the legacy config (user 2026-11-25); confirm with operator"),
    'Diag_IRGA': ('high', 'old invalid_count (7500_Warn) -> new valid_count'),
    'Diag_SONIC': ('high', 'old invalid_count (CSAT_Warn) -> new valid_count'),
    'Fm': ('high', 'old input missing from legacy config; Fm_Avg added from slow_flux'),
    'Wd_SONIC_Sd': ('high', 'old input missing from legacy config; WD_CSAT_Sd added from slow_met'),
    'RH_2m': ('high', 'old units frac, new percent; converted in L1'),
    'Fh': ('high', 'legacy compound instrument replaced by single CSAT3B (CLAUDE.md rule)'),
    'UyT': ('high', 'legacy compound instrument replaced by single CSAT3B'),
    'Tbody_RAD': ('none', 'new only: old logger stored the CNR4 thermistor resistance (Rs_CNR4_Avg), not a temperature'),
}
IRGA_NOTE = 'old IRGA relabelled LI-7500 -> LI-7500RS (logs signal strength; user 2026-11-25)'


def old_input(k, d):
    d = copy.deepcopy(d)
    inst = d['instrument']
    if isinstance(inst, dict):
        if k in ('Fh', 'UyT'):
            d['instrument'] = CSAT
        elif inst.get('irga') == 'LI-COR LI-7500':
            inst['irga'] = IRGA
    elif inst == 'LI-COR LI-7500':
        d['instrument'] = IRGA
    d['end'] = END
    return d


out = copy.deepcopy(NEW)
ff = {k: v for k, v in OLD['file_formats'].items() if k != SOIL}
out['file_formats'] = {**ff, **NEW['file_formats']}
old_vars = {VR.get(k, k): (k, v) for k, v in OLD['variables'].items()}
rows = []
for k, v in out['variables'].items():
    ivs = v['input_variables']
    new = ivs[0]
    if new['file'] == SOIL:
        continue
    if k in old_vars:
        ok, ov = old_vars[k]
        assert len(ov['input_variables']) == 1, k
        o = old_input(k, ov['input_variables'][0])
        if ok in VR:
            o['statistic_type'] = 'variance'
    elif k in EXTRA_OLD:
        o = dict(EXTRA_OLD[k], end=END)
    else:
        o = None
    conf, note = NOTES.get(k, ('high', ''))
    if o is None:
        rows.append((k, '-', '-', new['name'], new['file'][9:], new['units'], conf if k in NOTES else 'none', note))
        continue
    if ok in VR if k in old_vars else False:
        note = (note + '; ' if note else '') + 'old variance input square-rooted; new stdev passes through'
    if k not in ('Fh', 'UyT') and 'LI-7500' in str(ov['input_variables'][0]['instrument'] if k in old_vars else ''):
        note = (note + '; ' if note else '') + IRGA_NOTE
    new['begin'] = BEGIN
    v['input_variables'] = [o, new]
    rows.append((k, o['name'], o['file'][9:], new['name'], new['file'][9:], new['units'], conf, note))
for k in old_vars:
    if k not in out['variables']:
        assert k in DROP_OLD, f'unmapped legacy variable {k}'
        rows.append((k, old_vars[k][1]['input_variables'][0]['name'], '-', '-', '-', '-', 'dropped', DROP_OLD[k]))
for name, why in (
        ('Calperum_EC_slow_core (all)', 'subset duplicate of the other slow files; ends 2024-10-15'),
        ('Pressure106 / press_aux', 'auxiliary barometer, unmapped in both eras'),
        ('WindDir_Std_Dev@2m/@7m / Wd_aux_*_Sd', 'WindSentry direction Sd, unmapped in both eras'),
        ('Fe_raw_Avg / Fc_raw_Avg', 'pre-WPL fluxes; corrected Fe_Avg/Fc_Avg mapped')):
    rows.append(('-', name, '-', '-', '-', '-', 'unmapped', why))

yaml.safe_dump(out, open(OUT, 'w'), sort_keys=False, allow_unicode=True, width=200)
with open(OUT.replace('.yml', '_review.csv'), 'w', newline='') as f:
    w = csv.writer(f)
    w.writerow(['canonical', 'old_input', 'old_file', 'new_input', 'new_file', 'new_units', 'confidence', 'note'])
    w.writerows(rows)
print(Counter(r[6] for r in rows))
