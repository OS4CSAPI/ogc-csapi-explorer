# 03 Update Plan

## Phase 0 — Freeze and inventory
- export representative live resources
- record all current IDs and UIDs
- capture current Explorer behavior screenshots
- save bootstrap versions in use

## Phase 1 — Additive structural completion
Create, if missing:
- `String Alpha Localizer Feed` deployment leaf
- richer SET/reporting resource descriptions
- track SamplingFeature creation template/pattern

Do not remove anything yet.

## Phase 2 — Metadata enrichment
Enrich:
- deployments
- systems
- procedures
- datastreams

Add:
- plain-English descriptions
- doctrinal role descriptions
- provenance/source links
- media/document attachments
- state/lifecycle/owner metadata
- quality/freshness semantics

## Phase 3 — Schema upgrades
Upgrade the SET SENREP datastream to a richer schema profile:
- preserve doctrinal/reporting shape
- add stable join/provenance fields
- maintain compatibility with current demo workflow

## Phase 4 — Runtime verification
Verify:
- simulator still publishes
- localizer still computes
- click-to-report still works
- tracks are created consistently
- reset/resilience behavior still holds

## Phase 5 — UI verification
Verify:
- deployment-first navigation remains clear
- localizer is visible/understandable in the tree
- red SENREP markers, gold fixes, cyan trails, and purple track features remain coherent
- richer metadata is exposed in the detail views

## Hard requirements before execution
- no discovery logic should depend on brittle array position
- client must continue filtering around scope-leak behavior
- deployment/direct-association assumptions must account for dropped `deployment@link`
- track identity remains `contactId`-centered until link persistence is trustworthy
