# RETIRED 2026-11-25: the draft went live as operational/TiTreeEast.yml
# (and L2/TiTreeEast.yml); edit those directly from now on. Do NOT rerun
# this script: it reads operational/TiTreeEast.yml as the new-era source,
# so running it now would stitch the already-stitched config again. Kept as
# the record of how the stitched config was built.
#
# Generates the stitched TiTreeEast draft: legacy CR3000 era
# (legacy/TiTreeEast.yml, slow_core 2025-05-23 08:30 -> 2025-09-24 11:00) +
# TERNflux CR1000XE era (operational/TiTreeEast.yml, from 2025-09-24 14:00).
# Usage: python make_draft.py /opt/TERN_EP/site_configs/drafts/TiTreeEast/TiTreeEast.yml
# (also writes TiTreeEast_review.csv beside it). Once the draft goes live
# this script must be RETIRED (it reads operational/ as the new-era source).
#
# Decisions (user, 2026-11-25):
# - Every EC variable (sonic, IRGA, fluxes, covariances) at 10.0 m in both
#   eras, and the CNR4 at 10.0 m too (configs had 9.8/9.9/10.0 mixed).
# - Old-era Fco2/Fe left empty: the old program logged only uncorrected
#   fluxes (Fc_raw_Avg ~ covUzCc, Fe_raw_Avg); the old era's covariances are
#   stitched, so WPL can be done from them later.
# - Precip one series, sum, 1.5 m (provisional); Rimco RIM-7499-BOM ->
#   CS700 recorded in instrument history.
# - The 2021-22 daily slow_core archive on UQRDM is left out.
import copy, csv, sys
from collections import Counter
import yaml

BASE = '/opt/TERN_EP/site_configs'
NEW = yaml.safe_load(open(f'{BASE}/operational/TiTreeEast.yml'))
OLD = yaml.safe_load(open(f'{BASE}/legacy/TiTreeEast.yml'))
OUT = sys.argv[1]
END = '2025-09-24 11:00'
BEGIN = '2025-09-24 14:00'
HEIGHT = 10.0
CSAT3 = 'Campbell Scientific CSAT3'
SC = 'TiTreeEast_EC_slow_core'

VR = {'Tv_SONIC_Vr': 'Tv_SONIC_Sd', 'Ux_SONIC_Vr': 'Ux_SONIC_Sd',
      'Uy_SONIC_Vr': 'Uy_SONIC_Sd', 'Uz_SONIC_Vr': 'Uz_SONIC_Sd',
      'AH_IRGA_Vr': 'AH_IRGA_Sd', 'CO2c_IRGA_Vr': 'CO2c_IRGA_Sd'}
# Old variables mapped into a differently named new one.
RENAME = {'Ts_0.1ma': 'Ts_0.09ma'}
EXTRA_OLD = {
    'Fm': ({'name': 'Fm_Avg', 'instrument': CSAT3, 'units': 'kg/m/s^2', 'file': SC},
           'old input missing from legacy config; Fm_Avg added'),
    'Wd_SONIC_Sd': ({'name': 'WD_CSAT_Sd', 'instrument': CSAT3, 'units': 'degrees', 'file': SC},
                    'old input missing from legacy config; WD_CSAT_Sd added'),
    'Tbody_RAD': ({'name': 'Tb_CNR4_Avg', 'instrument': 'Kipp&Zonen CNR4', 'units': 'K', 'file': SC},
                  'old input missing from legacy config; Tb_CNR4_Avg (logged in K) added; Tb-Ta within 0.4 K in both eras'),
}
NEW_ONLY = {
    'Fco2': 'old era left empty: the old program logged only uncorrected Fc_raw_Avg (~covUzCc), no WPL (user 2026-11-25); old covariances are stitched',
    'Fe': 'old era left empty: the old program logged only uncorrected Fe_raw_Avg, no WPL (user 2026-11-25); old covariances are stitched',
}
EC_INSTRUMENTS = ('CSAT3', 'LI-7500', 'CNR4')
NOTES = {
    'Diag_IRGA': 'old invalid_count (7500_Warn) -> new valid_count',
    'Diag_SONIC': 'old invalid_count (CSAT_Warn) -> new valid_count',
    'Sig_IRGA': "PROVISIONAL: old raw column is AGC_7500_Avg (max 94, high = good), read as signal strength as at the other 'AGC' sites; confirm with operator",
    'Precip': 'statistic_type fixed average -> sum; Rimco RIM-7499-BOM (old, 2.0 m) -> CS700 (new); PROVISIONAL height 1.5 m for both eras (user 2026-11-25)',
    'Ts_0.09ma': 'old Ts_0.1ma (same TCAV, continuous at the changeover: 27.6 -> 27.0 degC) stitched into the operational name',
    'Sws_0.1ma': 'same CS616 profile: the new program names the four probes Sws_8cm[a-d] but values continue exactly at the changeover',
}
for k in ('Sws_0.35ma', 'Sws_0.6ma', 'Sws_0.85ma'):
    NOTES[k] = NOTES['Sws_0.1ma']


def is_ec(v):
    inst = v['input_variables'][-1]['instrument']
    names = inst.values() if isinstance(inst, dict) else [inst]
    return any(m in n for n in names for m in EC_INSTRUMENTS)


out = copy.deepcopy(NEW)
out['file_formats'] = {**OLD['file_formats'], **NEW['file_formats']}
old_vars = {RENAME.get(VR.get(k, k), VR.get(k, k)): (k, v) for k, v in OLD['variables'].items()}
rows = []
for k, v in out['variables'].items():
    new = v['input_variables'][0]
    assert len(v['input_variables']) == 1, k
    note = NOTES.get(k, '')
    conf = 'provisional' if 'PROVISIONAL' in note else 'high'
    if is_ec(v) and v['height'] != HEIGHT:
        note = (note + '; ' if note else '') + f"height {v['height']} -> {HEIGHT} m (user 2026-11-25)"
        v['height'] = HEIGHT
    if k == 'Precip':
        v['statistic_type'] = 'sum'
        v['height'] = 1.5
    if k in NEW_ONLY:
        rows.append((k, '-', '-', new['name'], new['file'][11:], new['units'], 'new-only', NEW_ONLY[k]))
        continue
    if k in old_vars:
        ok, ov = old_vars[k]
        assert len(ov['input_variables']) == 1, k
        o = copy.deepcopy(ov['input_variables'][0])
        if ok in VR:
            o['statistic_type'] = 'variance'
            note = (note + '; ' if note else '') + 'old variance input square-rooted; new stdev passes through'
    elif k in EXTRA_OLD:
        o, extra = EXTRA_OLD[k]
        o = copy.deepcopy(o)
        note = (note + '; ' if note else '') + extra
    else:
        raise SystemExit(f'no old-era mapping decided for {k}')
    o['end'] = END
    new['begin'] = BEGIN
    v['input_variables'] = [o, new]
    rows.append((k, o['name'], o['file'][11:], new['name'], new['file'][11:], new['units'], conf, note))
leftover = sorted(set(old_vars) - set(out['variables']))
assert not leftover, f'unmapped legacy variables: {leftover}'
for name, why in (
        ('Fc_raw_Avg / Fe_raw_Avg', 'old uncorrected fluxes, deliberately not mapped (see Fco2/Fe)'),
        ('PARin_Avg / Fpard_Avg', 'PAR, unmapped in both eras: PAR/Fsd at midday is 0.07 (old) and negative (new), physically ~2; calibration/wiring to check'),
        ('sws_cs650 / ec_cs650 / T_cs650 ...', 'CS650 probe in both eras, unmapped (not in either config)'),
        ('Ta_HMP_2m/RH_HMP_2m vs *_2m_Avg', 'mapped (Ta_2m/RH_2m)'),
        ('ps_CS106_Avg', 'auxiliary barometer, unmapped'),
        ('UQRDM 2021-05 -> 2022-05 daily slow_core/soil CSVs', 'earlier CR3000 record (program EC-TTE_May2021b), left out (user 2026-11-25)')):
    rows.append(('-', name, '-', '-', '-', '-', 'unmapped', why))

yaml.safe_dump(out, open(OUT, 'w'), sort_keys=False, allow_unicode=True, width=200)
with open(OUT.replace('.yml', '_review.csv'), 'w', newline='') as f:
    w = csv.writer(f)
    w.writerow(['canonical', 'old_input', 'old_file', 'new_input', 'new_file', 'new_units', 'confidence', 'note'])
    w.writerows(rows)
print(Counter(r[6] for r in rows))
