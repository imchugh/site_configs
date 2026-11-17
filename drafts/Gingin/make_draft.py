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
# Soil heat flux: only the three HFP01SCs remain (CN3s removed). PROVISIONAL:
# assumes Fg_01..03 are the old shf_Avg(1..3) plates, unmoved -- to confirm
# with the site operators.
for n,letter in ((1,'d'),(2,'e'),(3,'f')):
    M[f'Fg_0.08m{letter}']=(TF,f'Fg_0{n}','W/m^2','medium',f'PROVISIONAL: assumes Fg_0{n} is old shf_Avg({n}) HFP01SC, unmoved; new range ~4x smaller than old plates 2-3 (old CR3000 vs new CR1000X program: check sensitivity/self-cal); confirm with site operators')
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
        for d in v['input_variables'].values(): d['statistic_type']='variance'
        M[k[:-2]+'Sd']=(TF,VR[k][0],VR[k][1],'high','old variance input square-rooted; TERNflux stdev passes through')
out['variables']=renamed
rows=[]
for k in sorted(DERIVE):
    old_name=next(iter(out['variables'][k]['input_variables']))
    del out['variables'][k]
    rows.append((k,old_name,'-','-','-','-','derived','removed from config; fluxcore derives AH from Ta, RH and ps over the whole record'))
for k,v in out['variables'].items():
    ivs=v['input_variables']
    (old_name,old),=[(n,d) for n,d in ivs.items()][:1] if len(ivs)==1 else [list(ivs.items())[-1]]
    if old['file'].startswith('Gingin_soil'):
        continue
    if k in M:
        f,raw,u,conf,note=M[k]
        old['end']=OLD_END.get(k,END)
        new={'instrument':copy.deepcopy(INST.get(k,old['instrument'])),'units':u,'file':f,'begin':NEW_BEGIN.get(k,BEGIN)}
        if k.startswith('Diag_'): new['diag_type']='valid_count'
        ivs[raw]=new
        rows.append((k,old_name,old['file'][7:],raw,f[7:],u,conf,note+('; old era ends '+OLD_END[k]+' (sensor dead after)' if k in OLD_END else '')+('; new era begins '+NEW_BEGIN[k]+' (CNR4 body thermistor miswired before)' if k in NEW_BEGIN else '')))
    else:
        rows.append((k,old_name,old['file'][7:],'-','-','-','none',''))
yaml.safe_dump(out,open(OUT,'w'),sort_keys=False,allow_unicode=True,width=200)
import csv; w=csv.writer(open(OUT.replace('.yml','_review.csv'),'w'))
w.writerow(['canonical','old_input','old_file','new_input','new_file','new_units','confidence','note']); w.writerows(rows)
from collections import Counter; print(Counter(r[6] for r in rows))
