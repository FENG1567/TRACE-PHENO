# Public reproduction

Run `python scripts/reproduce_public.py` followed by `python scripts/verify_checksums.py` in the environment described by the root README. Public inputs are synthetic examples and aggregate results. The script builds all nine figure sets, validates the result registry and checks P0 ICU use against two independently preserved cohort partitions.

`figures/frozen/` contains the final exports: four main figures, four supplementary figures and a graphical abstract. Figure code and all 13 CSV inputs are in `figures/PublicationLayout/`; current figure numbers are mapped in [FIGURE_NUMBERING.md](FIGURE_NUMBERING.md). Rebuilding uses only those bundled inputs; no private fallback directory is consulted. The plot geometry and bold 18-point panel letters are retained from the submission version. Font fallback is described in the README.

The synthetic AP parser is an illustrative example rather than the original clinical text extractor. The restricted numerical scripts are included, but their required patient-level inputs are not. See `CREDENTIALLED_REPRODUCTION.md` for that separate workflow.
