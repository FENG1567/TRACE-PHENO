import csv
import importlib.util
from pathlib import Path
import tempfile
import unittest

ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('release_checks',ROOT/'scripts/check_release.py')
checks=importlib.util.module_from_spec(spec);spec.loader.exec_module(checks)

class RevisionAlignmentTests(unittest.TestCase):
    def test_current_result_lineage_matches_published_aggregate_sources(self):
        self.assertEqual(checks.validate_lineage(),[])

    def test_old_paired_interval_is_rejected(self):
        registry=ROOT/'results/manuscript_result_registry.csv'
        with registry.open(newline='',encoding='utf-8') as f:
            reader=csv.DictReader(f);rows=list(reader);fields=reader.fieldnames
        changed=next(r for r in rows if r['result_id']=='DOWNSTREAM-P1_minus_P0')
        changed['ci_lower']='-0.0345';changed['ci_upper']='-0.0244'
        with tempfile.TemporaryDirectory() as d:
            path=Path(d)/'registry.csv'
            with path.open('w',newline='',encoding='utf-8') as f:
                writer=csv.DictWriter(f,fieldnames=fields);writer.writeheader();writer.writerows(rows)
            errors=checks.validate_lineage(registry_path=path)
        self.assertTrue(any('Paired estimate/interval drift' in e for e in errors))

    def test_p3_cannot_be_relabelled_as_independent_clinical_performance(self):
        registry=ROOT/'results/manuscript_result_registry.csv'
        with registry.open(newline='',encoding='utf-8') as f:
            reader=csv.DictReader(f);rows=list(reader);fields=reader.fieldnames
        next(r for r in rows if r['phenotype']=='P3' and r['metric_name']=='rule_concordance')['metric_name']='sensitivity'
        with tempfile.TemporaryDirectory() as d:
            path=Path(d)/'registry.csv'
            with path.open('w',newline='',encoding='utf-8') as f:
                writer=csv.DictWriter(f,fieldnames=fields);writer.writeheader();writer.writerows(rows)
            errors=checks.validate_lineage(registry_path=path)
        self.assertIn('P3 must remain a separate rule-concordance result',errors)

    def test_registry_schema_accepts_csv_denominators_and_rejects_invalid_estimates(self):
        from trace_pheno.validation import validate_registry
        registry=ROOT/'results/manuscript_result_registry.csv'
        self.assertEqual(validate_registry(registry),[])
        with registry.open(newline='',encoding='utf-8') as f:
            reader=csv.DictReader(f);rows=list(reader);fields=reader.fieldnames
        rows[0]['estimate']='invalid-numeric-value'
        with tempfile.TemporaryDirectory() as d:
            path=Path(d)/'registry.csv'
            with path.open('w',newline='',encoding='utf-8') as f:
                writer=csv.DictWriter(f,fieldnames=fields);writer.writeheader();writer.writerows(rows)
            errors=validate_registry(path)
        self.assertTrue(any('registry schema row' in e for e in errors))

if __name__=='__main__':unittest.main()
