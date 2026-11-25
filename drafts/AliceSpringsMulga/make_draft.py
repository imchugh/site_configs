# RETIRED 2026-11-25: the draft went live as operational/AliceSpringsMulga.yml;
# edit that directly from now on. Do NOT rerun this script: it reads
# operational/AliceSpringsMulga.yml as the new-era source, so running it now
# would stitch the already-stitched config again. Kept as the record of how
# the stitched config was built.
#
# Generates the stitched AliceSpringsMulga draft. There is no legacy config:
# the old-era mapping below was built from the raw slow_core columns and
# checked against the data at the changeover (2026-11-25).
#
# Old era: CR6 (serial 18242, the same logger as now) running
# EC-ASM_Aug2022a.CR6, table slow_core: local files 2022-09-09 03:30 ->
# 2023-03-08 08:30 and 2024-06-30 23:00 -> 2025-04-10 07:30 (no data for
# 2023-03 -> 2024-06 anywhere). Old rain from the ancillary CR3000's
# slow_rain table (2024-09-13 -> 2025-04-10): slow_core's own Rain_Tot is 0
# throughout. New era: TERNflux from 2025-04-10 16:30, soil logger from
# 2025-04-10 13:59 (microsites) / 14:30 (VWC_Param).
# Usage: python make_draft.py /opt/TERN_EP/site_configs/drafts/AliceSpringsMulga/AliceSpringsMulga.yml
#
# Decisions (user, 2026-11-25):
# - Local CR6 files only; the UQRDM daily archive (CR3000 2021-05 -> 2022-07,
#   CR6 2022-08 -> 2022-09) is left for a later patch-file step.
# - Every EC variable at 11.6 m (the current config had 10.0 m on the
#   fluxes and gas covariances).
# - Soil TDR: only probes that continue at the changeover are stitched.
# - Wind profile (WS_WS_01-04, WS4) and profile thermocouples left out.
# - Old HMPs (HMP_01-04): heights unknown, so the old era of the air
#   temperature/humidity variables is left empty pending the operators.
# Following TiTreeEast: old Fco2/Fe left empty (the old program logged only
# uncorrected Fc_raw_Avg/Fe_raw_Avg); the old covariances are stitched.
import copy, csv, sys
from collections import Counter
import yaml

BASE = '/opt/TERN_EP/site_configs'
NEW = yaml.safe_load(open(f'{BASE}/operational/AliceSpringsMulga.yml'))
OUT = sys.argv[1]
END = '2025-04-10 07:30'
BEGIN = {'AliceSpringsMulga_EC_TERNflux': '2025-04-10 16:30',
         'AliceSpringsMulga_soil_soil_microsites': '2025-04-10 13:59',
         'AliceSpringsMulga_soil_VWC_Param': '2025-04-10 14:30'}
SC = 'AliceSpringsMulga_EC_slow_core'
RAIN = 'AliceSpringsMulga_ancl_slow_rain'
EC_HEIGHT = 11.6
LOGGER = 'Campbell Scientific CR6'

# canonical -> (old column, old units, file, note); variances marked 'variance'
OLD = {
    'Fh': ('Fh_Avg', 'W/m^2'), 'Fm': ('Fm_Avg', 'kg/m/s^2'), 'ustar': ('ustar_Avg', 'm/s'),
    'Tv_SONIC_Sd': ('covTvTv', 'degC^2', 'variance'),
    'UxT': ('covUxTv', 'm.degC/s'), 'UyT': ('covUyTv', 'm.degC/s'), 'UzT': ('covUzTv', 'm.degC/s'),
    'Ux_SONIC_Sd': ('covUxUx', 'm^2/s^2', 'variance'), 'Uy_SONIC_Sd': ('covUyUy', 'm^2/s^2', 'variance'),
    'Uz_SONIC_Sd': ('covUzUz', 'm^2/s^2', 'variance'),
    'UxUy': ('covUxUy', 'm^2/s^2'), 'UxUz': ('covUzUx', 'm^2/s^2'), 'UyUz': ('covUzUy', 'm^2/s^2'),
    'Ws_SONIC_Av': ('WS_CSAT_Avg', 'm/s'), 'Wd_SONIC_Av': ('WD_CSAT_Compass_Avg', 'degrees'),
    'Wd_SONIC_Sd': ('WD_CSAT_Sd', 'degrees'),
    'Ux_SONIC_Av': ('Ux_CSAT_Avg', 'm/s'), 'Uy_SONIC_Av': ('Uy_CSAT_Avg', 'm/s'), 'Uz_SONIC_Av': ('Uz_CSAT_Avg', 'm/s'),
    'Tv_SONIC_Av': ('Tv_CSAT_Avg', 'degC'),
    'Diag_SONIC': ('CSAT_Warn', 'dimensionless', 'invalid_count'),
    'Diag_IRGA': ('7500_Warn', 'dimensionless', 'invalid_count'),
    'CO2c_IRGA_Sd': ('covCcCc', 'mg^2/m^6', 'variance'), 'AH_IRGA_Sd': ('covAhAh', 'g^2/m^6', 'variance'),
    'UxC': ('covUxCc', 'mg/m^2/s'), 'UyC': ('covUyCc', 'mg/m^2/s'), 'UzC': ('covUzCc', 'mg/m^2/s'),
    'UxA': ('covUxAh', 'g/m^2/s'), 'UyA': ('covUyAh', 'g/m^2/s'), 'UzA': ('covUzAh', 'g/m^2/s'),
    'CO2c_IRGA_Av': ('Cc_7500_Avg', 'mg/m^3'), 'AH_IRGA_Av': ('Ah_7500_Avg', 'g/m^3'), 'ps': ('ps_7500_Avg', 'kPa'),
    'Sig_IRGA': ('sig_strn_7500_Avg', 'percent'),
    'Fsd': ('Fsd_CNR4_Avg', 'W/m^2'), 'Fsu': ('Fsu_CNR4_Avg', 'W/m^2'), 'Fld': ('Fld_CNR4_Avg', 'W/m^2'),
    'Flu': ('Flu_CNR4_Avg', 'W/m^2'), 'Tbody_RAD': ('Tb_CNR4_Avg', 'K'),
    'Tpanel': ('Tpanel_Avg', 'degC'), 'Vbat': ('Vbat_Avg', 'V'),
    'Fg_0.08ma': ('Fg_CN3_01_Avg', 'W/m^2'), 'Fg_0.08mb': ('Fg_CN3_02_Avg', 'W/m^2'), 'Fg_0.08mc': ('Fg_CN3_03_Avg', 'W/m^2'),
    'Ts_0.04ma': ('Ts_TCAV_01_Avg', 'degC'), 'Ts_0.04mb': ('Ts_TCAV_02_Avg', 'degC'), 'Ts_0.04mc': ('Ts_TCAV_03_Avg', 'degC'),
    'Sws_0.05ma': ('Sws_616_01', 'm^3/m^3'), 'Sws_0.05mb': ('Sws_616_02', 'm^3/m^3'), 'Sws_0.05mc': ('Sws_616_03', 'm^3/m^3'),
}
# TDR probes that continue at the changeover (old ToppVWC(i) -> new Sws_CS610(i),
# |last 2 h old - first 2 h new| <= 0.005 and the same number is the best or
# near-best match). 5, 6, 16, 20 and 21 don't: they were erratic on the old
# logger (24 h drops up to 0.29), so their old era is left out.
TDR_MATCH = {1, 2, 3, 4, 7, 8, 9, 10, 11, 12, 13, 14, 15, 17, 18, 19, 22}
NEW_ONLY = {
    'Fco2': 'old era empty: old program logged only uncorrected Fc_raw_Avg (no WPL), as at TiTreeEast; old covariances stitched',
    'Fe': 'old era empty: old program logged only uncorrected Fe_raw_Avg (no WPL), as at TiTreeEast; old covariances stitched',
    'Ta_11.6m': 'old era empty PENDING: old logger had four HMPs (HMP_01-04), heights unknown; confirm with operator (HMP_01 has the smallest diurnal range, so probably the top one)',
    'AH_11.6m': 'old era empty PENDING old HMP heights (see Ta_11.6m)',
    'RH_11.6m': 'old era empty PENDING old HMP heights (see Ta_11.6m)',
    'Ta_2m': 'old era empty PENDING old HMP heights (see Ta_11.6m)',
    'RH_2m': 'old era empty PENDING old HMP heights (see Ta_11.6m)',
}
NOTES = {
    'Diag_SONIC': 'old invalid_count (CSAT_Warn) -> new valid_count',
    'Diag_IRGA': 'old invalid_count (7500_Warn) -> new valid_count',
    'Sig_IRGA': 'old sig_strn_7500_Avg (genuine signal strength, median 100); AGC_7500_Avg not used',
    'Tbody_RAD': 'old Tb_CNR4_Avg logged in K',
    'Tpanel': 'logger relabelled CR1000XE -> CR6 in both eras: every file header (old and TERNflux) says CR6 serial 18242',
    'Vbat': 'logger relabelled CR1000XE -> CR6 in both eras: every file header (old and TERNflux) says CR6 serial 18242',
    'Fg_0.08ma': 'old CN3 plate 1 continues as microsites a (-2.01 -> -2.02 W/m^2 on the changeover day)',
    'Fg_0.08mb': 'old CN3 plate 2 -> microsites b: new channel empty on the first day, so continuity unchecked; PROVISIONAL',
    'Fg_0.08mc': 'old CN3 plate 3 -> microsites c: new channel empty on the first day, so continuity unchecked; PROVISIONAL',
    'Ts_0.04ma': 'old TCAV 1 continues as microsites a (27.8 -> 28.3 degC)',
    'Ts_0.04mb': 'old TCAV 2 -> microsites b: new channel empty on the first day; PROVISIONAL',
    'Ts_0.04mc': 'old TCAV 3 -> microsites c: new channel empty on the first day; PROVISIONAL',
    'Sws_0.05ma': 'old CS616 1 -> microsites a; new about 0.004 lower at the changeover (different logger calibration?); PROVISIONAL',
    'Sws_0.05mb': 'old CS616 2 -> microsites b; new about 0.005 lower at the changeover; PROVISIONAL',
    'Sws_0.05mc': 'old CS616 3 -> microsites c; new about 0.005 lower at the changeover; PROVISIONAL',
    'Precip': 'statistic_type fixed average -> sum; old era from the ancillary CR3000 slow_rain (2024-09-13 on); slow_core Rain_Tot is 0 throughout (gauge never wired to it), so no rain for 2022-09 -> 2024-09; PROVISIONAL gauge model (assumed the same CS700)',
}
EC_INST = ('CSAT3B', 'LI-7500RS')

out = copy.deepcopy(NEW)
out['file_formats'] = {SC: 'CSI', RAIN: 'CSI', **NEW['file_formats']}
rows = []
tdr = {f'Sws_CS610({i})': i for i in range(1, 23)}
for k, v in out['variables'].items():
    new = v['input_variables'][0]
    assert len(v['input_variables']) == 1, k
    note = NOTES.get(k, '')
    inst = new['instrument']
    names = inst.values() if isinstance(inst, dict) else [inst]
    if any(m in n for n in names for m in EC_INST) and v['height'] != EC_HEIGHT:
        note = (note + '; ' if note else '') + f"height {v['height']} -> {EC_HEIGHT} m (user 2026-11-25)"
        v['height'] = EC_HEIGHT
    if k == 'Precip':
        v['statistic_type'] = 'sum'
    if k in ('Tpanel', 'Vbat'):
        new['instrument'] = LOGGER
    old = None
    if k in OLD:
        spec = OLD[k]
        old = {'name': spec[0], 'instrument': copy.deepcopy(new['instrument']), 'units': spec[1], 'file': SC}
        if len(spec) > 2 and spec[2] == 'variance':
            old['statistic_type'] = 'variance'
            note = (note + '; ' if note else '') + 'old variance input square-rooted; new stdev passes through'
        elif len(spec) > 2:
            old['diag_type'] = spec[2]
    elif k == 'Precip':
        old = {'name': 'Rain_Tot', 'instrument': new['instrument'], 'units': 'mm', 'file': RAIN}
    elif new['name'] in tdr:
        i = tdr[new['name']]
        if i in TDR_MATCH:
            old = {'name': f'ToppVWC({i})', 'instrument': new['instrument'], 'units': 'm^3/m^3', 'file': SC}
            note = f'old TDR ToppVWC({i}) continues as Sws_CS610({i}) at the changeover'
        else:
            note = f'old era left out: old TDR ToppVWC({i}) does not continue as Sws_CS610({i}) (erratic before the changeover); confirm wiring with operator'
    elif k in NEW_ONLY:
        note = NEW_ONLY[k]
    else:
        raise SystemExit(f'no old-era decision for {k}')
    conf = 'provisional' if ('PROVISIONAL' in note or 'PENDING' in note) else 'high'
    if old is None:
        rows.append((k, '-', '-', new['name'], new['file'][18:], new['units'], 'new-only' if conf == 'high' else conf, note))
        continue
    old['end'] = END
    new['begin'] = BEGIN[new['file']]
    v['input_variables'] = [old, new]
    rows.append((k, old['name'], old['file'][18:], new['name'], new['file'][18:], new['units'], conf, note))
for name, why in (
        ('Ta/RH/Ah_HMP_01-04_Avg', 'four old HMPs; heights unknown: confirm with operator, then stitch the 11.6 m / 2 m ones and add the rest as old-only profile variables'),
        ('WS_WS_01-04_Avg, WS_WS4_Avg / WD_*', 'old wind profile, left out (user 2026-11-25); WS_WS_01 reads 0 (dead)'),
        ('TC_EC/200cm/425cm/650cm_Avg', 'old profile thermocouples, left out (user 2026-11-25); 200 cm and 650 cm broken'),
        ('Fc_raw_Avg / Fe_raw_Avg', 'old uncorrected fluxes, deliberately not mapped'),
        ('ToppVWC(5,6,16,20,21)', 'old TDRs that do not continue at the changeover, left out'),
        ('LaL(1-22)', 'TDR waveform lengths, unmapped'),
        ('ps_CS106_Avg, Tpanel_CR1000/storage', 'auxiliary barometer / other loggers\' panels, unmapped'),
        ('UQRDM AliceMulga daily CSVs', 'CR3000 2021-05 -> 2022-07 and CR6 2022-08 -> 2022-09, left for a later patch-file step (user 2026-11-25)')):
    rows.append(('-', name, '-', '-', '-', '-', 'unmapped', why))

yaml.safe_dump(out, open(OUT, 'w'), sort_keys=False, allow_unicode=True, width=200)
with open(OUT.replace('.yml', '_review.csv'), 'w', newline='') as f:
    w = csv.writer(f)
    w.writerow(['canonical', 'old_input', 'old_file', 'new_input', 'new_file', 'new_units', 'confidence', 'note'])
    w.writerows(rows)
print(Counter(r[6] for r in rows))
