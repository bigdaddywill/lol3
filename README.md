# LOL3 — Bid-to-Outreach Pipeline

LOL3 now contains a first functional, evidence-first pipeline for:

\`bid source -> normalized bid -> contractor match -> bid invitation -> email -> follow-up SMS\`

## Verified source artifacts

- \`hi\`: contractor TSV currently in the repo.
- \`[Concrete _ Indiana] 8 open bids last 14 days — nearest deadline Aug 25, 2026.eml\`: recovered reference bid digest.

The current \`hi\` dataset is parsed as TSV because the GitHub copy is a text export. The pipeline also exposes a dependency-free \`scrape_url()\` adapter for live HTML sources; source-specific parsers can be added without changing matching or outreach.

## Design rules

1. Matching is field-based and explainable.
2. Source evidence is preserved on every normalized bid.
3. Contractor qualifications are never inferred from category alone.
4. Every selected contractor receives match reasons and a score breakdown.
5. Outreach never states undocumented licensing/qualification facts.
6. Human approval remains the final send gate.

## Run locally

\`\`\`bash
python -m pipeline.bid_pipeline \
  --contractors hi \
  --source "[Concrete _ Indiana] 8 open bids last 14 days — nearest deadline Aug 25, 2026.eml" \
  --output artifacts/bid_pipeline.json
\`\`\`

Run tests:

\`python -m unittest discover -s tests -v\`

## Current audit boundary

The recovered email is a reference digest from Aug. 23, 2026. Its source listings are used here as an ingestion/parser fixture, not as proof that those bids are still open today.

The old digest scores are stored as source metadata only. LOL3 computes a separate contractor-match score from documented trade, state, scope, and contact fields.
