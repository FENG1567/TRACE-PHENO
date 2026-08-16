# Reproducibility levels

TRACE-PHENO uses three explicit reproduction levels.

## Level 1: public executable reproduction

Anyone can run the synthetic cases, parser boundaries, schema checks, P3/P4 equivalence, AKI reuse example, card generation, aggregate figure generation, and privacy scan.

## Level 2: aggregate numerical verification

Readers can trace each manuscript estimate to the public result registry, aggregate tables, and figure source rows. This level verifies reporting and visualization but cannot independently reconstruct patient-clustered bootstrap samples.

## Level 3: credentialled clinical reconstruction

Authorized researchers can reconstruct source cohorts and rerun the row-level analyses inside their own controlled environments. Database access, local mappings, and restricted derived files are prerequisites.

These levels are intentionally not conflated. Public code availability does not imply public patient-level data, and successful execution does not imply clinical validation.

