# Result lineage

The public result chain is:

`authorized source data → restricted source adapters → restricted row-level evidence assertions → aggregate analysis outputs → manuscript result registry → tables and figure source data → rendered figures`

Only the final aggregate layers are included here. The registry records the estimand, metric, numerator and denominator semantics, confidence-interval method, weighting method, source artifact, and analysis status. No metric should be inferred from row position or an unlabeled `estimate` field.

The revision-2 aggregate analysis corrected the target frame for formal-sample design weights: one representative hospitalization per sampled patient, with stratum weights derived from patient pools. It also rebuilt the eligible set separately for each label-boundary policy. The original analysis artifacts remain outside this public release; the correction is documented in `data/aggregate/benchmark/WEIGHT_CORRECTION_AUDIT.json`.

