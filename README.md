# TRACE-PHENO: auditable computable phenotyping

This repository accompanies a methods study of acute-pancreatitis (AP) computable phenotypes. It treats a phenotype definition as a documented measurement choice: each output retains its evidence requirements, missingness state, migration losses, and downstream consequences.

The repository is designed for public reproducibility without redistributing controlled clinical records. It contains code, machine-readable specifications, synthetic AP and AKI examples, aggregate non-identifying results, figure source tables, frozen figures, and automated checks. It does **not** contain patient-level records, clinical text, patient or hospital identifiers, credentials, or controlled source data.

## What can be reproduced publicly

- AP ICD value-set behavior and row-specific `3 × ULN` boundary handling.
- Parsing of `IU/L`, `U/L`, `Units/L`, and scientific notation.
- Transparent P0–P4 execution on synthetic AP cases.
- Exhaustive P3/P4 equivalence on complete binary three-domain inputs.
- Disease-generic schema reuse with a synthetic AKI time-window demonstration.
- Validation of the manuscript result registry and JSON specifications.
- Regeneration of publication figures from non-identifying aggregate source tables.
- Automated scans for forbidden identifiers, absolute local paths, and obvious credentials.

## What requires credentialed data

The patient-clustered bootstrap, blinded two-clinician adjudication of the reference set, and row-level cohort derivation require the original controlled databases and restricted intermediate files. Those data cannot be placed on GitHub. The required input contract is provided in [`schemas/credentialed_validation_inputs.schema.json`](schemas/credentialed_validation_inputs.schema.json), while [`docs/CREDENTIALLED_REPRODUCTION.md`](docs/CREDENTIALLED_REPRODUCTION.md) describes the authorized route. The restricted row-level analysis script is not included in this public release.

The study reports exploratory conditional agreement against a **constructed reference set** built through blinded, independent adjudication by two experienced surgical clinicians, with disagreements resolved by a third surgical clinician. Cross-database results concern operational portability, mapping loss, evidence coverage, phenotype-positive yield, and negative capability.

## Quick start

Python 3.11 or newer is recommended.

```bash
python -m venv .venv
python -m pip install --upgrade pip
python -m pip install -e .
python scripts/reproduce_public.py
python scripts/verify_checksums.py
```

On Windows systems where `python` points to a legacy application runtime, use `py -3.12` for the same commands.

Expected result: all unit tests pass, P3/P4 equivalence is confirmed within its declared scope, public figures are regenerated under `artifacts/figures`, and the public-package scan reports `PASS`.

Individual commands:

```bash
trace-pheno synthetic
trace-pheno equivalence
trace-pheno cards
trace-pheno validate
python scripts/build_figures.py
```

## Repository map

| Path | Purpose |
|---|---|
| `src/trace_pheno` | Public rules, parser, equivalence checker, cards, and validation |
| `configs` | Frozen phenotype, database-role, transport, and D0–D6 specifications |
| `schemas` | Disease-generic and result-registry contracts |
| `data/synthetic` | Fully public synthetic AP and AKI inputs |
| `data/aggregate` | Non-identifying aggregate analysis and figure source data |
| `results` | Manuscript result registry, tables, supplementary tables, and generated cards |
| `figures/frozen` | Frozen manuscript figures and alt text |
| `tests` | Boundary, equivalence, schema, and privacy tests |
| `docs` | Reproduction, data-access, limitations, and provenance documentation |
| `manifests` | Public asset inventory, checksums, and privacy/license audit |

## Data and evidence boundary

MIMIC, eICU, NWICU, SICdb, and HiRID remain subject to their source access and use terms. This repository neither grants access to those databases nor changes their licenses. DATASUS was excluded because the local completeness gate did not pass. See [`docs/DATA_AVAILABILITY.md`](docs/DATA_AVAILABILITY.md).

## Citation and archiving

Use [`CITATION.cff`](CITATION.cff) after replacing the contributor placeholder with the final author list. GitHub is a version-control host, not a permanent scholarly archive. After release, archive the tagged version in a repository such as Zenodo and add the resulting DOI to this README and `CITATION.cff`; no DOI is claimed here.

## License

The original code and documentation in this repository are released under the MIT License. This license does not apply to the source clinical databases. Aggregate tables retain the scientific attribution and source-data restrictions described in [`DATA_LICENSE.md`](DATA_LICENSE.md).
