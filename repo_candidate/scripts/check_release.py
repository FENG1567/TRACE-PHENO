"""Check current result lineage, manuscript tables and nine rebuilt figure sets."""
from pathlib import Path
import csv
import json
import math
from PIL import Image

ROOT=Path(__file__).resolve().parents[1]
def read(path):
    with path.open(encoding='utf-8-sig',newline='') as f:return list(csv.DictReader(f))
def validate_lineage(root=ROOT, registry_path=None):
    errors=[]
    registry=read(registry_path or root/'results/manuscript_result_registry.csv')
    def same(a,b):
        try:return math.isclose(float(a),float(b),rel_tol=0,abs_tol=1e-12)
        except (ValueError,TypeError):return False
    clinical=[m for m in read(root/'data/aggregate/revision/BENCHMARK_METRICS.csv')
              if m['policy']=='strict' and m['scale']=='design_weighted' and m['phenotype'] in ('P0','P1','P2')]
    for m in clinical:
        found=[r for r in registry if r['phenotype']==m['phenotype'] and r['metric_name']==m['metric']]
        if len(found)!=1:errors.append('Clinical registry row missing or duplicated: '+m['phenotype']+'/'+m['metric']);continue
        if any(not same(found[0][k],m[k]) for k in ('estimate','ci_lower','ci_upper')) or found[0]['ci_method']!=m['ci_method']:
            errors.append('Clinical estimate/interval drift: '+m['phenotype']+'/'+m['metric'])
    for m in read(root/'data/aggregate/revision/MIMIC_PAIRED_DOWNSTREAM_BOOTSTRAP.csv'):
        found=[r for r in registry if r['result_id']=='DOWNSTREAM-'+m['comparison']]
        if len(found)!=1:errors.append('Paired registry row missing or duplicated: '+m['comparison']);continue
        if not same(found[0]['estimate'],m['point_difference_B_minus_A']) or any(not same(found[0][k],m[k]) for k in ('ci_lower','ci_upper')) or found[0]['ci_method']!=m['ci_method']:
            errors.append('Paired estimate/interval drift: '+m['comparison'])
    for r in registry:
        if not (root/r['source_artifact'].split('#')[0]).is_file():errors.append('Missing result source: '+r['source_artifact'])
        if r['phenotype']=='P3' and r['metric_name']!='rule_concordance' and not r['result_id'].startswith('COHORT-'):
            errors.append('P3 must remain a separate rule-concordance result')
    tables=root/'results/tables'
    expected={'Table_1_Phenotype_Definitions.csv','Table_2_Database_Capabilities.csv','Table_3_Conditional_Agreement.csv','Table_4_Downstream_Consequences.csv','Table_5_Summary.csv'}
    if {p.name for p in tables.glob('*.csv')}!=expected:errors.append('Main table names/order mismatch')
    summary=read(tables/'Table_5_Summary.csv')
    if list(summary[0])!=['Summary'] or len(summary)!=4:errors.append('Table 5 summary must contain one Summary column and four rows')
    if sorted(p.name.split('_')[2] for p in (root/'results/supplementary_tables').glob('*.csv')) != [f'{i:02}' for i in range(1,15)]:
        errors.append('Supplementary table inventory mismatch')
    burden={r['phenotype']:r for r in read(root/'figures/PublicationLayout/source_data/frozen/Figure_5_Burden.csv')}
    main=read(tables/'Table_4_Downstream_Consequences.csv')
    icu=next(k for k in main[0] if 'icu' in k.lower())
    main_p0=next(r for r in main if list(r.values())[0]=='P0')
    if not same(main_p0[icu],burden['P0']['icu_pct']):errors.append('P0 main-table ICU summary differs from aggregate')
    for obsolete in ('data/aggregate/benchmark','data/aggregate/figure_source'):
        if (root/obsolete).exists():errors.append('Obsolete result directory: '+obsolete)
    return errors

def validate_figures(root=ROOT):
    errors=[]
    stems={p.stem for p in (root/'figures/frozen').glob('*.pdf')}
    output=root/'artifacts/figures'
    expected_stems={
        'Figure_1_Study_Design','Figure_2_Conditional_Agreement','Figure_3_Transportability',
        'Figure_4_Downstream_Consequences','Supplementary_Figure_1_Construct_and_Reference',
        'Supplementary_Figure_2_Label_Policy_Sensitivity','Supplementary_Figure_3_P3_P4_Rule_Concordance',
        'Supplementary_Figure_4_Generic_Framework','Graphical_Abstract',
    }
    if stems!=expected_stems:errors.append('Frozen figure filenames do not match the current nine-set numbering')
    for stem in sorted(stems):
        for ext in ('.pdf','.svg','_preview.png','.tif'):
            if not (output/(stem+ext)).is_file():errors.append('Missing rebuilt export: '+stem+ext)
        with Image.open(output/(stem+'.tif')) as image:
            if any(abs(float(d)-600)>1 for d in image.info.get('dpi',(0,0))):errors.append('TIFF resolution mismatch: '+stem)
    return errors

if __name__=='__main__':
    errors=validate_lineage()+validate_figures()
    print(json.dumps({'status':'FAIL' if errors else 'PASS','errors':errors,'figure_sets':9},indent=2))
    raise SystemExit(bool(errors))
