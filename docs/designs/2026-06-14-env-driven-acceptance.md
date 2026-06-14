# Env-Driven Acceptance Initialization

## Context

The acceptance console currently rebuilds its runtime data with hardcoded station topology: 3 fast chargers, 2 slow chargers, queue length 3, and waiting area capacity 10. This conflicts with `backend/.env`, where station counts and queue sizes are supposed to be configurable. A second issue appears after executing all acceptance events: snapshot history and table views can collapse to only the final/current state instead of the full event history.

Complexity: medium. The fix touches backend initialization and snapshot history plus frontend table rendering.

## Goals

- Acceptance initialization uses the same runtime configuration as normal backend startup.
- Backend restart automatically initializes a fresh runtime database from `.env`.
- Acceptance table columns are derived from snapshot station data instead of fixed station names.
- Executing to final state preserves and displays the full snapshot history.

## Non-Goals

- No schema redesign.
- No change to acceptance event parsing semantics.
- No visual redesign beyond making existing views dynamic.

## Risks

- Automatic startup reset is destructive to runtime data. This matches the current request and local acceptance workflow, but production deployments should opt out if needed.
- Snapshot history ordering must remain stable after multiple snapshots at the same time.

## TODO

- [x] Backend: make startup/runtime initialization and acceptance scenario creation read `.env` runtime config.
  - Scope: `backend/app/config.py`, `backend/app/utils/db.py`, `backend/app/services/acceptance_service.py`, docs/env examples if needed.
  - Validation: backend tests around configured station topology.
- [x] Backend: preserve full acceptance snapshot history after `execute_all`.
  - Scope: `backend/app/services/acceptance_service.py`.
  - Validation: targeted acceptance test that executes all events and sees before/after/final snapshots.
- [x] Frontend: remove fixed acceptance station columns.
  - Scope: `frontend/src/views/admin/Acceptance.vue`.
  - Validation: frontend build and code inspection for dynamic station columns.
- [x] Review and verification pass.
  - Scope: changed files only.
  - Validation: backend pytest subset and frontend build.

## Validation Results

- `python3 -m unittest backend.tests.test_acceptance_export -v` passed.
- `npm run build` passed in `frontend/`.
- `python3 -m pytest backend/tests/test_acceptance_export.py -q` could not run because `pytest` is not installed in the local Python environment; the same tests were run with `unittest`.
- `python3 -m unittest backend.tests.test_frozen_contracts -v` still has pre-existing expectation mismatches around legacy user IDs and detail fields; the failures are outside the acceptance/env changes covered here.
