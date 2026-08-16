# Credentialled full reproduction

Full clinical reproduction requires authorized access to each source database and a local restricted workspace. Do not copy protected data into this repository or a GitHub Actions runner.

## Required restricted inputs

The input contract is described in `schemas/credentialed_validation_inputs.schema.json`. The revision-2 analysis uses:

1. a reference-set table with a non-public case key and frozen reference label;
2. phenotype predictions derived from authorized source records;
3. a patient-level development/validation split;
4. the sampling frame and stratum-specific pool and sample counts.

## Recommended route

1. Obtain the required credential and complete the data-use training for each database.
2. Create a restricted directory outside the Git repository.
3. Rebuild source-specific mappings from `results/supplementary_tables/Supplementary_Table_9_Field_Level_Mapping.csv`.
4. Keep all row-level intermediates in the restricted environment.
5. Implement or obtain the restricted analysis workflow within the authorized environment, using the published input contract and aggregate output definitions.
6. Move only the aggregate outputs through the privacy scan before public release.
7. Compare the resulting SHA-256 values and numerical tolerances with the public aggregate artifacts.

The restricted row-level analysis script is not included in this public release. The public repository provides the input contract, aggregate outputs, and reporting definitions needed to inspect the analysis boundary, but it cannot independently reconstruct the patient-level bootstrap or reference-set analyses.
