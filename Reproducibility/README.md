# Authorized numerical reproduction

The scripts in `Reproducibility/` stage inputs from the original frozen TRACE-PHENO project and rerun the reference, transport and paired downstream analyses. Run a copy of this directory in an authorized workspace outside the public Git checkout. Keep every staged row-level file there.

The source project must contain `03_reference_standard`, `05_transport`, `06_downstream` and the source audit scripts under `code/audit`. Reference staging uses `DEV_VALIDATION_SPLIT.csv`, the selected reference-label CSV, `PACKET_MANIFEST.csv`, `SAMPLING_WEIGHTS.json` and `CANDIDATE_FRAME.csv`. The label CSV must contain `review_case_id`, `variant` and `final_label` columns. If more than one matching label CSV is present, select the intended file explicitly with `--reference-label-file`; a relative path is resolved under `<project-root>/03_reference_standard`. Transport/downstream JSON inputs are read from the corresponding frozen source directories; the exact filenames are in `stage_inputs.py`.

```bash
cd /path/to/authorized/workspace/Reproducibility
python stage_inputs.py --project-root /path/to/authorized/trace_pheno --reference-label-file /path/to/authorized/trace_pheno/03_reference_standard/selected_reference_labels.csv
python run_server_analysis.py
```

Replace `selected_reference_labels.csv` with the exact file chosen for the run. A sole matching candidate is accepted by default; multiple candidates produce an error listing the available files and the required option. `TRACE_PHENO_PROJECT_ROOT` may replace `--project-root`. Staging validates the source layout before writing `inputs/`. It produces four analysis files: `validation_inputs.csv`, `sampling_design_inputs.csv`, `mimic_patient_cluster_counts.csv` and `aggregate_context_inputs.json`. `input_manifest.json` records the selected label source filename, project-relative path and SHA-256; the analysis summary carries those values into its reference provenance.

The numerical output is written to `outputs/`. Reference estimates use 5,000 stratified patient-bootstrap replicates (seed 20260816); downstream contrasts use 2,000 paired patient-cluster replicates (seed 20260815), preserving repeated draws. The exact script versions are copied from this package. Compare eligible counts, estimates, interval endpoints and interval methods with `data/aggregate/revision/`; regenerated file hashes can differ with runtime or serialization changes.

The source staging step uses an existing frozen project, not raw databases alone. Public aggregate reproduction and synthetic examples do not recreate clinical adjudication or original clinical-text extraction. Do not place their inputs in a public repository.

The public cohort-summary check can be run from the repository root with `python Reproducibility/check_cohort_summary.py`.
