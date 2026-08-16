# FAIR and repository checklist

## Findable

- Machine-readable metadata: `CITATION.cff` and `pyproject.toml`.
- Stable filenames and a SHA-256 manifest.
- A future tagged release should be archived with a DOI; no DOI is currently claimed.

## Accessible

- Code, schemas, synthetic data, aggregate results, and figures are directly accessible.
- Controlled clinical data remain accessible only through their source platforms and qualifications.

## Interoperable

- Core objects are expressed as JSON Schema and CSV dictionaries.
- Transport states and D0–D6 failure codes have explicit vocabularies.
- UTF-8 is used throughout.

## Reusable

- The repository includes a license, citation metadata, data boundary, environment files, tests, CI, source tables, provenance documentation, and known limitations.
- Final authors and repository URL must be added before public release.

