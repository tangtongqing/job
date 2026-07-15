# TASK-QA-REWORK-002 Review

**Conclusion: Not accepted.**

**Reviewed:** 2026-07-10  
**Scope:** `GET /api/v1/applications` returns a job summary without N+1 queries.

## What Passed

- The endpoint returns HTTP 200 with paginated `{data, meta}` envelope.
- Each list item contains `job.id`, `job.company`, and `job.title`, matching the frontend requirement and the documented list contract.
- The endpoint bulk-loads the job records; it does not issue one job query per application.
- Full backend suite passes: `91 passed`.

## Blocking Finding

`ApplicationOut.model_validate(a).model_dump()` serializes the `events` relationship for every list item even though the list contract does not return events. With three applications, the endpoint executed six SELECT statements:

1. total count;
2. paginated applications;
3. batch job lookup;
4. one `application_event` lookup for application 1;
5. one `application_event` lookup for application 2;
6. one `application_event` lookup for application 3.

This is a backend N+1 query regression. It grows linearly with the page size and conflicts with the stated purpose of the rework.

## Required Rework

1. Serialize the list response with a dedicated list schema or explicit scalar dictionary that excludes `events`; do not call an ORM serializer that lazy-loads detail-only relationships.
2. Keep the existing bulk job lookup and the `job` summary fields.
3. Add a focused `GET /applications` regression test for the job summary. Include query-count or lazy-load prevention coverage so the event N+1 issue cannot return.
4. Re-run the full backend suite and provide the list endpoint's actual response evidence.
