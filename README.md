# TRACE-PHENO reproducibility package

This package accompanies “Evidence availability and diagnosis semantics alter acute pancreatitis cohorts and downstream conclusions: the TRACE-PHENO audit framework”. It contains the code, aggregate results and figure sources for the major revision, plus synthetic examples of AP and AKI rules.

## Reproduce the public outputs

Use Python 3.12 in a clean environment. From the repository root:

```bash
python -m venv .venv
# Activate .venv using your operating system's standard command.
python -m pip install -r requirements-lock.txt
python -m pip install --no-deps -e .
python scripts/reproduce_public.py
python scripts/verify_checksums.py
```

`scripts/reproduce_public.py` runs the unit tests, synthetic examples, P3/P4 complete-binary-input equivalence check, cards, aggregate consistency checks and all nine figure sets. Generated outputs are written to `artifacts/`; the submission figures are retained in `figures/frozen/`. PDFs and SVGs preserve vector content; TIFF exports are 600 dpi.

```bash
python scripts/build_figures.py --out artifacts/figures
python Reproducibility/check_cohort_summary.py
trace-pheno synthetic
trace-pheno equivalence
```

The layouts prefer Arial, followed by Liberation Sans and DejaVu Sans. Install a licensed Arial font for the submission typography, or set `TRACE_PHENO_FONT_FAMILY` to an installed font. Font and rendering-library differences can change pixels across machines; the frozen submission exports remain available for comparison.

## Results and files

| Path | Contents |
|---|---|
| `src/trace_pheno`, `data/synthetic` | Illustrative synthetic rules and inputs |
| `data/aggregate/revision` | Nine current aggregate analysis tables |
| `results/tables` | Four main tables in manuscript order |
| `results/supplementary_tables` | Fourteen supplementary source tables in manuscript order |
| `results/manuscript_result_registry.csv` | Current estimates, intervals, methods and source links |
| `figures/PublicationLayout` | Current figure code and 13 aggregate source CSVs |
| `figures/frozen` | Six main figures, two supplementary figures and graphical abstract |
| `Reproducibility` | Restricted-input staging and numerical analysis scripts; public aggregate checker |
| `configs`, `schemas` | Definitions, database releases and input contracts |
| `manifests` | Asset inventory and checksums |

The clinical comparison contains P0–P2. P3 is reported separately as rule concordance; P5 is retained as a specification. The principal-position versus any-position mortality contrast uses paired patient-cluster bootstrap intervals that preserve draw multiplicity. P0 ICU use is 656/3,266, or 20.1% at manuscript precision.

The synthetic AP examples illustrate rule and numeric-boundary behavior. They are not the clinical text extractor and do not reproduce the original admission-relative evidence extraction. The AKI example is synthetic software reuse. The reference labels were established through two clinicians' independent review and third-clinician adjudication.

## Authorized clinical reproduction

The included `Reproducibility/stage_inputs.py` and `run_server_analysis.py` require the original frozen project layout and authorized source artifacts. These scripts do not reconstruct the original clinical text extraction from raw databases alone. See [the restricted workflow](docs/CREDENTIALLED_REPRODUCTION.md) and [input contract](schemas/credentialed_validation_inputs.schema.json).

Patient-level records, reference-review packets, clinical narratives, original identifiers and restricted staged inputs are not bundled. Source databases retain their access and use conditions. Public aggregate figure rebuilding requires none of those inputs.

## Citation and license

Software citation metadata are in `CITATION.cff`. Original code and documentation use the MIT License. Source clinical databases are governed by their own terms, as described in `DATA_LICENSE.md`.
