# 03 Update Plan

## Phase 0 — Freeze current state
- export current ISS family
- document current IDs and discovery assumptions
- save screenshots/Explorer behavior for comparison

## Phase 1 — Additive structural build
Create:
- deployments
- systems
- procedures
- datastreams

Do not remove existing ISS branch yet.

## Phase 2 — Publisher migration
Update the publisher to discover:
- deployments/systems/datastreams by stable UID/name
- not by server-generated ID or array position

Start with position publishing only, then add orbit-track publishing.

## Phase 3 — Metadata enrichment
Add rich descriptive metadata to:
- deployments
- systems
- procedures
- datastreams

Include:
- official source links
- method links
- image/document/media attachments
- cadence/freshness/quality semantics

## Phase 4 — Verification
- verify datastream round-trip
- verify Explorer rendering
- verify deployment-first navigation
- verify observation-derived track behavior still works
- verify no hardcoded ID dependency remains

## Phase 5 — Cleanup
Optionally:
- alias old resources
- retire old flat ISS branch
- document final truth source and ownership

## Hard requirements before execution
- stable naming/UID conventions chosen
- TLS behavior understood
- retry/backoff implemented in publisher
- datastream discovery does not use array position
