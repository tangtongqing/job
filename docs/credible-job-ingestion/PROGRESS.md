# Credible Job Ingestion Progress

## Status: Phase 1 - Complete

## Decisions

- Use public Greenhouse Job Board APIs for real collection.
- Configure Figma, Webflow, Intercom and Stripe as independent sources.
- Keep deterministic demo snapshots for offline presentation.
- Keep BOSS and Nowcoder disabled; do not bypass access controls.

## Completed

- Verified current API availability and relevant product-role counts for selected boards.
- Audited current field coverage and identified the seed/log credibility gap.
- Added a reusable Greenhouse public Job Board API adapter and four independently configured sources.
- Expanded the deterministic snapshot to 24 complete jobs with honest `demo_snapshot` provenance.
- Added full JD, exact-heading requirement extraction, official apply/source URLs and English experience parsing.
- Added source discovery and field-completeness API contracts.
- Rebuilt the crawler UI around real source state, demo/live counts, quality metrics and honest logs.
- Updated job list/detail source labels, demo disclosure and primary official application action.
- Reset and collected a live verification dataset: 56 total jobs (24 demo + 32 public API).
- Verified data quality: JD 100%, apply URL 100%, source URL 100%, requirements 98%.
- Verified 107 backend tests, frontend lint and 14-route production build.

## Future

- Add durable scheduling and incremental refresh for long-term personal use.
- Add automatic link verification and freshness retirement policies.
- Add more public ATS providers only after their official access and terms are verified.
