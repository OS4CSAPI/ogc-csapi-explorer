# 00 Implementation Order

## Build sequence
1. Freeze the current live-server inventory and export what exists.
2. Preserve the current deployment backbone and confirm all leaf semantics.
3. Add the missing localizer/reporting structural resources additively.
4. Enrich deployments with role/purpose/state metadata.
5. Enrich systems with identity/provenance/media metadata.
6. Enrich procedures with method inputs/outputs/assumptions/docs.
7. Upgrade the SENREP schema to the richer reporting shape.
8. Add or normalize track SamplingFeature creation semantics.
9. Verify simulator → localizer → click-to-report → SENREP → track workflow end-to-end.
10. Only after the enriched branch works should you retire or alias thinner legacy shapes.

## Why this order
- It preserves rollback.
- It does not break the live demo while adding richer structure.
- It treats deployments as first-class while still allowing new operational producer/reporting resources to be introduced.
- It applies metadata enrichment after the key structural decisions are explicit.
