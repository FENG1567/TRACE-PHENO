# Authorized numerical reproduction

The scripts in `Reproducibility/` stage inputs from the original frozen TRACE-PHENO project and rerun the reference, transport and paired downstream analyses. Run a copy of this directory in an authorized workspace outside the public Git checkout. Keep every staged row-level file there.

The source project must contain `03_reference_standard`, `05_transport`, `06_downstream` and the source audit scripts under `code/audit`. Reference staging uses `DEV_VALIDATION_SPLIT.csv`, `REFERENCE_LABEL_SET.csv`, `PACKET_MANIFEST.csv`, `SAMPLING_WEIGHTS.json` and `CANDIDATE_FRAME.csv`. Transport/downstream JSON inputs are read from the corresponding frozen source directories; the exact filenames are in `stage_inputs.py`.

```bash
cd /path/to/authorized/workspace/Reproducibility
python stage_inputs.py --project-root /path/to/authorized/trace_pheno
python run_server_analysis.py
```

`TRACE_PHENO_PROJECT_ROOT` may replace `--project-root`. Staging validates the source layout before writing `inputs/`. It produces four analysis files: `validation_inputs.csv`, `sampling_design_inputs.csv`, `mimic_patient_cluster_counts.csv` and `aggregate_context_inputs.json`.

The numerical output is written to `outputs/`. Reference estimates use 5,000 stratified patient-bootstrap replicates (seed 20260816); downstream contrasts use 2,000 paired patient-cluster replicates (seed 20260815), preserving repeated draws. The exact script versions are copied from this package. Compare eligible counts, estimates, interval endpoints and interval methods with `data/aggregate/revision/`; regenerated file hashes can differ with runtime or serialization changes.

The source staging step uses an existing frozen project, not raw databases alone. Public aggregate reproduction and synthetic examples do not recreate clinical adjudication or original clinical-text extraction. Do not place their inputs in a public repository.

The numerical source run used Python 3.12.3, NumPy 1.26.4 and SciPy 1.11.4. `Reproducibility/requirements-recorded.txt` records those numerical-library versions for a separate authorized environment. The root dependency lock describes public-package and figure verification; it is not evidence of a new patient-level analysis.
