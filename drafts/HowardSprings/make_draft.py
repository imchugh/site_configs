# RETIRED 2026-11-25: the draft went live as operational/HowardSprings.yml
# (and L2/HowardSprings.yml); edit those directly from now on. Do NOT rerun
# this script: it reads operational/HowardSprings.yml as the new-era source,
# so running it now would stitch the already-stitched config again. Kept as
# the record of how the stitched config was built.
#
# Generates the stitched HowardSprings draft: legacy CR3000 era
# (legacy/HowardSprings.yml, 2022-11-16 17:30 -> 2025-09-08 17:30) + TERNflux
# CR1000XE era (operational/HowardSprings.yml, from 2025-10-13 14:00).
# Usage: python make_draft.py /opt/TERN_EP/site_configs/drafts/HowardSprings/HowardSprings.yml
# (also writes HowardSprings_review.csv beside it). Once the draft goes live
# this script must be RETIRED (it reads operational/ as the new-era source).
#
# Decisions (user, 2026-11-25):
# - EC height is 23 m for every EC variable in both eras: the operational
#   config's 10 m on Fco2/Fe/Fh/Fm and the gas covariances was a config error.
# - Precip is one series, statistic_type sum, at the old 0.6 m (the
#   operational config had average at 1.0 m).
# - Old-era RH: the old program measured RH but output only the AH it
#   calculated from it, so RH_23m/RH_2m's old era is a calculated input
#   (calculate_from AH + Ta, fluxcore derivation_history records it).
# - Real instrument changes stay per era: CSAT3 -> CSAT3B, LI-7500A ->
#   LI-7500RS, HMP45C -> HMP155, CR3000 -> CR1000XE.
import copy, csv, sys
from collections import Counter
import yaml

BASE = '/opt/TERN_EP/site_configs'
NEW = yaml.safe_load(open(f'{BASE}/operational/HowardSprings.yml'))
OLD = yaml.safe_load(open(f'{BASE}/legacy/HowardSprings.yml'))
OUT = sys.argv[1]
END = '2025-09-08 17:30'
BEGIN = '2025-10-13 14:00'
EC_HEIGHT = 23.0
CSAT3 = 'Campbell Scientific CSAT3'
FL, EB = 'HowardSprings_EC_flux', 'HowardSprings_EC_EnrgyBal'

VR = {'Tv_SONIC_Vr': 'Tv_SONIC_Sd', 'Ux_SONIC_Vr': 'Ux_SONIC_Sd',
      'Uy_SONIC_Vr': 'Uy_SONIC_Sd', 'Uz_SONIC_Vr': 'Uz_SONIC_Sd',
      'AH_IRGA_Vr': 'AH_IRGA_Sd', 'CO2c_IRGA_Vr': 'CO2c_IRGA_Sd'}
# Old inputs present in the raw files but missing from the legacy config.
EXTRA_OLD = {
    'Fm': ({'name': 'tau', 'instrument': CSAT3, 'units': 'kg/m/s^2', 'file': FL},
           'old input missing from legacy config; tau added from EC_flux'),
    'Wd_SONIC_Sd': ({'name': 'std_wnd_dir', 'instrument': CSAT3, 'units': 'degrees', 'file': FL},
                    'old input missing from legacy config; std_wnd_dir added from EC_flux'),
    'Tbody_RAD': ({'name': 'Lbody_temp_Avg', 'instrument': 'Kipp&Zonen CNR4', 'units': 'K', 'file': EB},
                  'old input missing from legacy config; Lbody_temp_Avg (logged in K) added from EC_EnrgyBal'),
}
# Old era calculated: the HMP45C's RH was measured but only its AH was output.
CALC = {f'RH_{h}': [f'AH_{h}', f'Ta_{h}'] for h in ('23m', '2m')}
NOTES = {
    'Diag_IRGA': 'old invalid_count (irga_warnings) -> new valid_count',
    'Diag_SONIC': 'old invalid_count (csat_warnings) -> new valid_count',
    'Sig_IRGA': "PROVISIONAL: old raw column is named agc_Avg (max 88, high = good), read as signal strength as at the other 'AGC' sites; confirm with operator",
    'Precip': 'statistic_type fixed average -> sum; PROVISIONAL height 0.6 m (old CS700 height) for both eras (user 2026-11-25); confirm new-era height with operator (operational config said 1.0 m)',
    'Tpanel': 'logger CR3000 -> CR1000XE; height 2.0 m (new) for both eras (old config said 1.0 m)',
    'Vbat': 'logger CR3000 -> CR1000XE; height 2.0 m (new) for both eras (old config said 1.0 m)',
    'Ws_SONIC_Av': '', 'Fg_0.08mc': 'old era only: no third plate on the new logger (hfp_3 already all-NaN by Aug 2025)',
    'Fg_0.08md': 'old era only: no fourth plate on the new logger (hfp_4 already all-NaN by Aug 2025)',
}
# The flux-system variables whose operational height was wrongly 10 m.
EC_VARS = {'Fco2', 'Fe', 'Fh', 'Fm', 'UxA', 'UyA', 'UzA', 'UxC', 'UyC', 'UzC'}


def old_input(d):
    d = copy.deepcopy(d)
    d['end'] = END
    return d


out = copy.deepcopy(NEW)
out['file_formats'] = {**OLD['file_formats'], **NEW['file_formats']}
old_vars = {VR.get(k, k): (k, v) for k, v in OLD['variables'].items()}
rows = []
for k, v in out['variables'].items():
    new = v['input_variables'][0]
    assert len(v['input_variables']) == 1, k
    note = NOTES.get(k, '')
    conf = 'provisional' if 'PROVISIONAL' in note else 'high'
    if k in EC_VARS and v['height'] != EC_HEIGHT:
        v['height'] = EC_HEIGHT
        note = (note + '; ' if note else '') + f'height 10 -> {EC_HEIGHT} m: operational config error (user 2026-11-25)'
    if k == 'Precip':
        v['statistic_type'] = 'sum'
        v['height'] = 0.6
    if k in ('Tpanel', 'Vbat'):
        v['height'] = 2.0
    new['begin'] = BEGIN
    if k in CALC:
        o = {'calculate_from': CALC[k], 'instrument': 'Vaisala HMP45C', 'end': END}
        note = 'old era calculated from ' + ' + '.join(CALC[k]) + ' (HMP45C RH was measured but only AH was output); recorded in derivation_history'
        rows.append((k, 'calculated', '-', new['name'], new['file'][14:], new['units'], 'high', note))
    elif k in old_vars:
        ok, ov = old_vars[k]
        assert len(ov['input_variables']) == 1, k
        o = old_input(ov['input_variables'][0])
        if ok in VR:
            o['statistic_type'] = 'variance'
            note = (note + '; ' if note else '') + 'old variance input square-rooted; new stdev passes through'
        rows.append((k, o['name'], o['file'][14:], new['name'], new['file'][14:], new['units'], conf, note))
    elif k in EXTRA_OLD:
        o, extra_note = EXTRA_OLD[k]
        o = old_input(o)
        note = (note + '; ' if note else '') + extra_note
        rows.append((k, o['name'], o['file'][14:], new['name'], new['file'][14:], new['units'], conf, note))
    else:
        raise SystemExit(f'no old-era mapping decided for {k}')
    v['input_variables'] = [o, new]
# Old-only variables (sensors the new logger doesn't have): keep as they were.
for k, (ok, ov) in old_vars.items():
    if k not in out['variables']:
        out['variables'][k] = copy.deepcopy(ov)
        i = ov['input_variables'][0]
        rows.append((k, i['name'], i['file'][14:], '-', '-', '-', 'old-only', NOTES.get(k, '')))
for name, why in (
        ('Quntm_down/up_Avg / Fpard/Fparu_Avg', 'PAR, unmapped in both eras (not in operational config). NB both eras give PAR/Fsd ~0.9 umol/J at midday, physically ~2: calibration to check before mapping'),
        ('Rn_Avg / Rn_NR_corr_Avg / Fn_Avg', 'logger net radiation, unmapped (fluxcore always calculates Fn)'),
        ('SKYE_* / RED_/NIR_/GREEN_/BLUE_*', 'spectral sensors, unmapped'),
        ('CO2_GMM220_Avg', 'GMM220 CO2 probe, unmapped'),
        ('Fc_irga / LE_irga / wpl terms', 'uncorrected fluxes and WPL terms, unmapped; corrected Fc_wpl/LE_wpl mapped'),
        ('HowardSprings_EC_UWAflux / diagnostic / tip_timer', 'other tables, unmapped')):
    rows.append(('-', name, '-', '-', '-', '-', 'unmapped', why))

yaml.safe_dump(out, open(OUT, 'w'), sort_keys=False, allow_unicode=True, width=200)
with open(OUT.replace('.yml', '_review.csv'), 'w', newline='') as f:
    w = csv.writer(f)
    w.writerow(['canonical', 'old_input', 'old_file', 'new_input', 'new_file', 'new_units', 'confidence', 'note'])
    w.writerows(rows)
print(Counter(r[6] for r in rows))
