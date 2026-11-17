# Result lineage

The released clinical aggregates are in `data/aggregate/revision/`. The registry reads strict design-weighted P0–P2 estimates from `BENCHMARK_METRICS.csv`, their raw and weighted confusion counts from `BENCHMARK_CONFUSION.csv`, P3 concordance from `P3_RULE_CONCORDANCE.csv`, and the four downstream contrasts from `MIMIC_PAIRED_DOWNSTREAM_BOOTSTRAP.csv`. Every registry source path is repository-relative; a fragment identifies the selected row.

Tables 1–4 follow the current manuscript order for phenotype definitions, database capabilities, conditional agreement, and downstream consequences. Table 5 contains the concise narrative summary. Supplementary source tables are numbered 01–14. Their values are copied from the revision package, and main-table cells were read from the actual final English DOCX using WPS.

Contrast intervals preserve repeated patient draws. Zero-width boundary intervals use the method recorded in the current aggregate CSVs. P0 ICU use is 656/3,266 (20.1%), consistent with the preserved disjoint cohort summaries.

The registry schema describes CSV strings as returned by `csv.DictReader`. Estimate and interval fields use numeric strings; empty intervals are allowed for summaries without confidence intervals. A contrast denominator retains both cohort sizes as `B=...; A=...`. The validator checks actual registry rows against this schema.
