# Data availability

This public repository contains only synthetic inputs and non-identifying aggregate outputs.

| Source | Publicly redistributed here? | Reproduction route | Role in the study |
|---|---:|---|---|
| MIMIC | No | Obtain credentialed access from the source platform, then run the credentialed workflow locally | Blinded two-clinician reference adjudication, exploratory conditional agreement, downstream analysis |
| eICU | No | Obtain source access and rebuild the documented mappings | Multi-hospital structured transportability and reportability |
| NWICU | No | Obtain source access under its terms | Structured replication and ULN-aware mapping |
| SICdb | No | Obtain source access under its terms | Small-sample execution boundary |
| HiRID | No | Obtain source access under its terms | Negative capability; AP not identifiable without a diagnosis domain |
| DATASUS local extract | No | Not used in formal results because the completeness gate did not pass | Excluded |

The repository does not contain clinical narratives, row-level derived records, sampling lists, review packets, patient keys, hospital identifiers, or credentials. Access to a source database does not automatically authorize redistribution of its derived row-level files.

Publicly shared material comprises:

- fully synthetic AP and AKI cases;
- aggregate confusion matrices and summary estimates;
- figure source tables with no hospital identifiers;
- manuscript and supplementary tables;
- code, specifications, schemas, tests, and audit manifests.

