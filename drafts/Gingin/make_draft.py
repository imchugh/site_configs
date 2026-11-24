# Regenerates the stitched Gingin draft from the live operational config.
# Usage: python make_draft.py /opt/TERN_EP/site_configs/drafts/Gingin/Gingin.yml
# (also writes Gingin_review.csv beside it). Open questions: see the review CSV.
import yaml, copy, sys
SRC='/opt/TERN_EP/site_configs/operational/Gingin.yml'
OUT=sys.argv[1]
END='2026-10-20 11:30'; BEGIN='2026-10-20 12:00'
TF='Gingin_EC_TERNflux'; AN='Gingin_ancillary_ancillary_data'
# canonical -> (file, raw name, units, confidence, note); instrument copied from old input unless given
M={
 'AH_IRGA_Av':(TF,'H2O_mean','g/m^3','high',''),
 'CO2c_IRGA_Av':(TF,'CO2_mean','mg/m^3','high',''),
 'ps':(TF,'amb_press_mean','kPa','high',''),
 'Fco2':(TF,'Fco2','mg/m^2/s','high',''),
 'Fe':(TF,'Fe','W/m^2','high',''),
 'Fh':(TF,'Fh','W/m^2','high',''),
 'Fm':(TF,'tau','kg/m/s^2','high',''),
 'ustar':(TF,'u_star','m/s','high',''),
 'UxT':(TF,'Tsonic_Ux_cov','m.degC/s','high',''),
 'UyT':(TF,'Tsonic_Uy_cov','m.degC/s','high',''),
 'UzT':(TF,'Tsonic_Uz_cov','m.degC/s','high',''),
 'UxUy':(TF,'Ux_Uy_cov','m^2/s^2','high',''),
 'UxUz':(TF,'Ux_Uz_cov','m^2/s^2','high',''),
 'UyUz':(TF,'Uy_Uz_cov','m^2/s^2','high',''),
 'UxA':(TF,'H2O_Ux_cov','g/m^2/s','high',''),
 'UyA':(TF,'H2O_Uy_cov','g/m^2/s','high',''),
 'UzA':(TF,'H2O_Uz_cov','g/m^2/s','high',''),
 'UxC':(TF,'CO2_Ux_cov','mg/m^2/s','high',''),
 'UyC':(TF,'CO2_Uy_cov','mg/m^2/s','high',''),
 'UzC':(TF,'CO2_Uz_cov','mg/m^2/s','high',''),
 'Ux_SONIC_Av':(TF,'Ux_Avg','m/s','high',''),
 'Uy_SONIC_Av':(TF,'Uy_Avg','m/s','high',''),
 'Uz_SONIC_Av':(TF,'Uz_Avg','m/s','high',''),
 'Tv_SONIC_Av':(TF,'Tsonic_Avg','degC','high',''),
 'Ws_SONIC_Av':(TF,'wnd_spd','m/s','high',''),
 'Wd_SONIC_Av':(TF,'wnd_dir_compass','degrees','high',''),
 'Wd_SONIC_Sd':(TF,'std_wnd_dir','degrees','high',''),
 'Sig_IRGA':(TF,'sig_str_irga_Avg','percent','high',''),
 'Diag_SONIC':(TF,'sonic_samples_Tot','dimensionless','high','old invalid_count (CSAT_Warn) -> new valid_count; per-input diag_type (fluxcore a1091b8)'),
 'Diag_IRGA':(TF,'irga_samples_Tot','dimensionless','high','old invalid_count (7500_Warn) -> new valid_count; per-input diag_type (fluxcore a1091b8)'),
 'Fsd':(TF,'Fsd_Avg','W/m^2','high','confirmed: no height change'),
 'Fsu':(TF,'Fsu_Avg','W/m^2','high','confirmed: no height change'),
 'Fld':(TF,'Fld_Avg','W/m^2','high','confirmed: no height change'),
 'Flu':(TF,'Flu_Avg','W/m^2','high','confirmed: no height change'),
 'Tbody_RAD':(TF,'Tb_Avg','K','high','confirmed: no height change'),
 'Precip':(TF,'rain_Tot','mm','high','confirmed: no height change'),
 'Tpanel':(TF,'Tpanel_Avg','degC','high','logger now CR1000X',),
 'Vbat':(TF,'Vbat_Avg','V','high','logger now CR1000X'),
 'Ta_15m':(TF,'Ta_sensor_mean','degC','high','confirmed: EC-height HMP is the old 14.7 m one'),
 'RH_15m':(TF,'RH_sensor_mean','percent','high','confirmed: EC-height HMP is the old 14.7 m one'),
 'AH_15m':(TF,'AH_sensor_mean','g/m^3','high','confirmed: EC-height HMP is the old 14.7 m one'),
 'Ws_16m':(TF,'Ws_Av','m/s','high','confirmed: Ws_Av/Wd_Av is the old 15.5 m Windsonic'),
 'Wd_16m':(TF,'Wd_Av','degrees','high','confirmed: Ws_Av/Wd_Av is the old 15.5 m Windsonic'),
}
# Soil heat flux (user, 2026-11-24): the new logger's three plates are NOT the
# old ones. They're Hukseflux HFP01s (not self-calibrating, unlike the old
# HFP01SCs), buried at 16 cm (old plates: 8 cm) in new locations, so they're
# new variables with new letters g/h/i, not a continuation of the 8 cm series.
# The old CN3 (a-c) and HFP01SC (d-f) variables keep their old inputs only.
# All three new channels give coherent data (r >= 0.978 with each other since
# 2026-10-20); the user thought only two were operational, so all three are
# mapped until the operators say which.
NEW_FG={f'Fg_0.16m{letter}':(f'Fg_0{n}','Hukseflux HFP01','W/m^2')
        for n,letter in ((1,'g'),(2,'h'),(3,'i'))}
NEW_FG_HEIGHT=-0.16
# Shallow soil: PROVISIONAL, to confirm with the site operators. The new
# logger has two real CS650s (slot 3 exactly duplicates slot 2 in every output
# except an empty sws -- a program fault, ignored) and two TCAV averages
# (Tsoil_mean(3) empty). Assumed: Tsoil_mean(1/2) = old TCAV a/b at 4 cm,
# cs650(1) = old 6 cm probe; cs650(2) unmapped until its depth is known.
for n,letter in ((1,'a'),(2,'b')):
    M[f'Ts_0.04m{letter}']=(TF,f'Tsoil_mean({n})','degC','medium',f'PROVISIONAL: assumes Tsoil_mean({n}) is old TCAV{letter} at 4 cm; confirm with site operators')
M['Sws_0.06m']=(TF,'sws_cs650_Avg(1)','m^3/m^3','medium','PROVISIONAL: assumes CS650 slot 1 is the old 6 cm probe; slot 2 depth unknown, slot 3 duplicates slot 2 (program fault); confirm with site operators')
M['Ts_0.06m']=(TF,'T_cs650_Avg(1)','degC','medium','PROVISIONAL: assumes CS650 slot 1 is the old 6 cm probe; slot 2 depth unknown, slot 3 duplicates slot 2 (program fault); confirm with site operators')
for h in ('2m','4m','7m','10m'):
    M[f'Ta_{h}']=(AN,f'Ta_{h}_Avg','degC','high','ancillary logger; assumes same height')
    M[f'RH_{h}']=(AN,f'RH_{h}_Avg','percent','high','ancillary logger; assumes same height')
    M[f'Ws_{h}']=(AN,f'Ws_{h}_Av','m/s','high','ancillary logger; assumes same height')
    M[f'Wd_{h}']=(AN,f'Wd_{h}_Av','degrees','high','ancillary logger; assumes same height')
# Variances: the old logger stored variance, TERNflux stores standard deviation.
# Rename X_Vr -> X_Sd (what fluxcore outputs anyway), keep the old input as a
# variance input, add the TERNflux stdev as the new input.
VR={'Tv_SONIC_Vr':('Tsonic_stdev','degC'),'Ux_SONIC_Vr':('Ux_stdev','m/s'),
    'Uy_SONIC_Vr':('Uy_stdev','m/s'),'Uz_SONIC_Vr':('Uz_stdev','m/s'),
    'AH_IRGA_Vr':('H2O_stdev','g/m^3'),'CO2c_IRGA_Vr':('co2_stdev','mg/m^3')}
# Old inputs that end before the changeover: the 7 m and 10 m WS4 Windsonics
# died after 2023-01-25 18:30 (logged 0s until removed from the program in
# Oct 2023), so their old eras stop at the last real reading.
OLD_END={k:'2023-01-25 18:30' for k in ('Ws_7m','Wd_7m','Ws_10m','Wd_10m')}
# New inputs that start after the changeover: the new CNR4 body thermistor was
# miswired until a site visit (last bad reading 2026-11-10 09:30, missing
# 10:00-12:30, valid from 13:00). Fld/Flu are corrected with it, so all three
# start at the fix; the miswired period is unsalvageable (user, 2026-11-16).
NEW_BEGIN={k:'2026-11-10 13:00' for k in ('Tbody_RAD','Fld','Flu')}
# Profile AH: the HMP155s measure Ta/RH only; the old logger calculated AH.
# Dropped so fluxcore derives AH from Ta, RH and ps over the whole record with
# one method (user, 2026-11-17). The 15 m AH stays: both eras are logged.
DERIVE={f'AH_{h}' for h in ('2m','4m','7m','10m')}
# New sensors with no old-logger counterpart, added from the changeover
# (user, 2026-11-17). Models from the logger program (Apogee SQ-110-SS pair,
# S/N 31316 in / 31418 out; Apogee SI-111). Heights not in the program:
# assumed on the 15 m radiation boom, to confirm with the site operators.
# Note: the program copy in ~/Documents names PAR Fpard/Fparu, but the loaded
# program writes Fqd/Fqu, so these names change if that copy is ever loaded.
NEW={'Fqd':('Fqd_Avg','Apogee Instruments SQ-110-SS','umol/m^2/s'),
     'Fqu':('Fqu_Avg','Apogee Instruments SQ-110-SS','umol/m^2/s'),
     'Tcanopy':('Ttarg_IR_C_Avg','Apogee Instruments SI-111-SS','degC')}
NEW_HEIGHT=15.0
# Water table depth from the CS451 in the bore (installed once, never moved;
# user, 2026-11-17). Every era maps the RAW level -- metres of water above the
# probe, rising as the water table rises -- so L1 is one measurement end to
# end. L2 turns it into CF water_table_depth (positive down) with one
# undated linear correction: WTD = 13.173 - level (L2/Gingin.yml). The new
# program's WL_CS451_DTW/AHD outputs are left out (derived on the logger; the
# old program's were 0.0 from 2024). 13.173 = 9.81 m dip to water + 3.363 m
# above the probe at install, but the first logged reading (2022-08-05) is
# 3.507, so the true probe depth may be 13.317: to confirm with operators.
WTD_INPUTS=[('CS451_Level','Gingin_EC_slow_met',None,'2023-01-25 18:30'),
            ('CS451_Level_Avg','Gingin_EC_slow_met','2023-01-25 19:00',END),
            ('CS451_Level_Avg',TF,BEGIN,None)]
WTD_HEIGHT=-13.173
INST={'Tpanel':'Campbell Scientific CR1000X','Vbat':'Campbell Scientific CR1000X'}

c=yaml.safe_load(open(SRC))
out=copy.deepcopy(c)
out['file_formats'][TF]='CSI'; out['file_formats'][AN]='CSI'
out['flux_file']=TF
renamed={}
for k,v in list(out['variables'].items()):
    renamed[k[:-2]+'Sd' if k in VR else k]=v
    if k in VR:
        v['statistic_type']='standard_deviation'
        for d in v['input_variables']: d['statistic_type']='variance'
        M[k[:-2]+'Sd']=(TF,VR[k][0],VR[k][1],'high','old variance input square-rooted; TERNflux stdev passes through')
out['variables']=renamed
rows=[]
for k in sorted(DERIVE):
    old_name=out['variables'][k]['input_variables'][0]['name']
    del out['variables'][k]
    rows.append((k,old_name,'-','-','-','-','derived','removed from config; fluxcore derives AH from Ta, RH and ps over the whole record'))
for k,v in out['variables'].items():
    ivs=v['input_variables']
    old=ivs[-1]; old_name=old['name']
    if old['file'].startswith('Gingin_soil'):
        continue
    if k in M:
        f,raw,u,conf,note=M[k]
        old['end']=OLD_END.get(k,END)
        new={'name':raw,'instrument':copy.deepcopy(INST.get(k,old['instrument'])),'units':u,'file':f,'begin':NEW_BEGIN.get(k,BEGIN)}
        if k.startswith('Diag_'): new['diag_type']='valid_count'
        ivs.append(new)
        rows.append((k,old_name,old['file'][7:],raw,f[7:],u,conf,note+('; old era ends '+OLD_END[k]+' (sensor dead after)' if k in OLD_END else '')+('; new era begins '+NEW_BEGIN[k]+' (CNR4 body thermistor miswired before)' if k in NEW_BEGIN else '')))
    else:
        rows.append((k,old_name,old['file'][7:],'-','-','-','none',''))
for k,(raw,inst,u) in NEW.items():
    out['variables'][k]={'statistic_type':'average','height':NEW_HEIGHT,'input_variables':[{'name':raw,'instrument':inst,'units':u,'file':TF,'begin':BEGIN}]}
    rows.append((k,'-','-',raw,TF[7:],u,'new',f'new sensor, no old counterpart; PROVISIONAL height {NEW_HEIGHT} m (radiation boom assumed); confirm with site operators'))
for k,(raw,inst,u) in NEW_FG.items():
    out['variables'][k]={'statistic_type':'average','height':NEW_FG_HEIGHT,'input_variables':[{'name':raw,'instrument':inst,'units':u,'file':TF,'begin':BEGIN}]}
    rows.append((k,'-','-',raw,TF[7:],u,'new','new HFP01 (not self-calibrating) at 16 cm in a new location; replaces the 8 cm plates (user 2026-11-24). All 3 channels look live; user thought only 2 operational: confirm with site operators'))
ivs=[]
for raw,f,b,e in WTD_INPUTS:
    d={'name':raw,'instrument':'Campbell Scientific CS451','units':'m','file':f}
    if b: d['begin']=b
    if e: d['end']=e
    ivs.append(d)
out['variables']['WTD']={'statistic_type':'average','height':WTD_HEIGHT,'input_variables':ivs}
rows.append(('WTD','CS451_Level / CS451_Level_Avg','EC_slow_met','CS451_Level_Avg',TF[7:],'m','new','raw level (m of water above probe) in every era, incl. the old sampled CS451_Level to 2023-01-25; L2 converts to depth with WTD = 13.173 - level. PROVISIONAL constant: first reading 3.507 vs install 3.363 suggests 13.317; confirm with site operators'))
yaml.safe_dump(out,open(OUT,'w'),sort_keys=False,allow_unicode=True,width=200)
import csv; w=csv.writer(open(OUT.replace('.yml','_review.csv'),'w'))
w.writerow(['canonical','old_input','old_file','new_input','new_file','new_units','confidence','note']); w.writerows(rows)
from collections import Counter; print(Counter(r[6] for r in rows))
