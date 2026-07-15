# TASK-QA-REWORK-003 | P2 Polish and Visual Evidence

## Background and Goal

`TASK-QA-001` identified several P2 issues that do not block the core workflow but reduce the project’s product quality and portfolio credibility. P1 rework is now accepted. Complete this bounded P2 pass and provide real browser screenshots for the affected desktop and mobile views.

The goal is a more reliable, legible product surface without changing backend contracts, state-machine behavior, or the existing product information architecture.

## Allowed Read Paths

- `web/`
- `docs/design/`
- `docs/product/`
- `.agent-ops/TASK-QA-001-FINAL-REVIEW.md`
- `.agent-ops/TASK-QA-REWORK-002-FINAL-REVIEW.md`
- `.agent-ops/TASK-QA-REWORK-003-REVIEW.md`
- `.agent-ops/visual-checks/`

## Allowed Write Paths

- `web/app/`
- `web/components/`
- `web/lib/`
- `.agent-ops/visual-checks/TASK-QA-REWORK-003/`
- `.agent-ops/mimo/outbox/TASK-QA-REWORK-003-result.md`

## Prohibited Actions

- Do not modify `src/`, API contracts, database models, or state-machine behavior.
- Do not add dependencies, third-party services, credentials, telemetry, or external API calls.
- Do not redesign the marketing page, change copy strategy, or perform unrelated refactors.
- Do not claim screenshot coverage without actual image files in the required evidence directory.
- Do not leave a development server or browser process running after evidence capture.

## Implementation Requirements

1. **Font loading:** remove the render-blocking Google Fonts CSS `@import`. Use the project’s supported Next.js font mechanism where buildable without adding dependencies; preserve reasonable system-font fallbacks and the existing display/body font roles.
2. **Mobile app navigation:** replace the horizontally scrolling text navigation in `web/app/(app)/layout.tsx` with a compact menu opened by an icon button. Use Lucide `Menu` / `X` icons, preserve access to all five app routes, theme toggle, API status, and the return-home action. The menu must be keyboard accessible and close after selecting a route.
3. **Dashboard trend:** improve `TrendChart` so every bar has an accessible date/value label and a clear hover/focus data affordance. Keep the chart compact; date labels must remain readable at a 390px viewport.
4. **Crawler safety clarity:** BOSS and Nowcoder are currently fail-closed sources. Present them as unavailable/disabled controls with an explicit “will be skipped” explanation. They must not issue a crawl request when clicked. Keep the company-site source usable.
5. **Operation feedback:** add a small global toast/notification primitive using existing React/Tailwind facilities only. Integrate it into the app shell and use it for user-triggered success/failure actions on at least applications state transition/batch transition, create application, and crawler trigger. Existing inline errors may remain; no silent failure is allowed.
6. Preserve loading, empty, and offline behavior. Do not alter current API client envelopes or endpoint paths.

## Visual Evidence Requirements

1. Start the local frontend only for verification and capture real browser screenshots at both `1366x768` and `390x844`.
2. Save all images under `.agent-ops/visual-checks/TASK-QA-REWORK-003/` with descriptive names.
3. Required coverage:
   - `/` at desktop and mobile: verify marketing CTA still reaches `/dashboard`.
   - `/dashboard` at desktop and mobile: verify chart labels and app navigation.
   - `/crawler` at desktop and mobile: verify disabled BOSS/Nowcoder controls.
   - `/applications` at desktop: verify toast-visible success or failure state using a controlled local backend response, if feasible.
4. If a browser cannot be launched, report the exact blocker and do not state that visual evidence was completed. The code work may still be submitted, but the task will not be accepted until screenshots are supplied.

## Verification Commands

- `cd web && npm.cmd run lint` -> no warnings or errors.
- `cd web && npm.cmd run build` -> production build succeeds.
- Capture and list the required browser screenshot files -> all required routes and viewports present.

## Result File

Write the final report to:

```text
.agent-ops/mimo/outbox/TASK-QA-REWORK-003-result.md
```

## Result Format

```markdown
# TASK-QA-REWORK-003 result

## Summary

## Modified Files

## Requirement-by-Requirement Evidence

## Commands and Results

## Visual Evidence
| file | route | viewport | verified behavior |
|---|---|---|---|

## Remaining Risks or Blockers
```
