# Credible Job Ingestion Implementation

## Phase 1: Public ATS ingestion

- [ ] Add Greenhouse adapter with filtering, retries and structured extraction.
- [ ] Support multiple configured sources using one adapter.
- [ ] Support non-empty YAML lists in crawler configuration.
- [ ] Add adapter and configuration tests.

Success: a fake API fixture and at least one live public board can produce jobs with JD and official links.

## Phase 2: Complete deterministic demo data

- [ ] Expand the seed to at least 24 complete jobs.
- [ ] Populate JD, requirements, official career links, education, experience and verification metadata.
- [ ] Replace simulated success logs with an explicit demo initialization record.

Success: after demo reset, core detail fields and external-link coverage are 100% for seeded jobs.

## Phase 3: Source and data-quality visibility

- [ ] Add source status API.
- [ ] Add field completeness statistics.
- [ ] Render enabled sources, quality metrics and honest log messages in crawler UI.

Success: the user can distinguish demo data from real ingestion and can trigger each enabled public source.

## Phase 4: Verification and handoff

- [ ] Run backend tests.
- [ ] Run frontend lint and production build.
- [ ] Reset demo and validate field coverage through the live API.
- [ ] Browser-test jobs, details and crawler management.
- [ ] Update project progress and README.
