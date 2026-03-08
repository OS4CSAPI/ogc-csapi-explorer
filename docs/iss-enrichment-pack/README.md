# ISS Implementation-Ready Pack v2

This pack is intended to be much closer to "ready for use" for the ISS resource family.

It includes:
- the target deployed-system-first model
- before/after structural diff
- execution/update plan
- metadata enrichment profile
- data source + ingestion flow
- media/image placement guidance
- a resource-by-resource enrichment matrix
- implementation-ready JSON templates for deployments, systems, procedures, datastreams, and example observations
- an asset/document manifest with suggested official links and image placements
- acceptance tests and a rollout checklist

## Important notes
1. These templates are designed to be adapted to your OSH/CSAPI conventions, not blindly POSTed without validation.
2. The pack intentionally treats Deployments/Subdeployments as the primary consumer-facing backbone.
3. The pack distinguishes:
   - tracked asset identity (ISS as the thing of interest),
   - producer systems (publishers/track generators),
   - procedures (SGP4 propagation, orbit-track generation),
   - products (position fixes, orbit-track products).
4. Until the server reliably persists richer FOI links, result payloads carry stable asset identity fields (`noradId`, `assetName`).

## Recommended file order
1. `00_IMPLEMENTATION_ORDER.md`
2. `01_RESOURCE_FAMILY_TARGET_MODEL.md`
3. `02_BEFORE_AFTER_STRUCTURAL_DIFF.md`
4. `03_UPDATE_PLAN.md`
5. `04_METADATA_ENRICHMENT_PROFILE.md`
6. `05_DATA_SOURCE_AND_INGESTION_FLOW.md`
7. `06_MEDIA_AND_IMAGE_PLACEMENT_GUIDE.md`
8. `07_RESOURCE_BY_RESOURCE_ENRICHMENT_MATRIX.md`
9. `08_JSON_TEMPLATES/*`
10. `09_ASSET_AND_DOCUMENT_MANIFEST.md`
11. `10_ACCEPTANCE_TESTS_AND_CHECKLIST.md`
