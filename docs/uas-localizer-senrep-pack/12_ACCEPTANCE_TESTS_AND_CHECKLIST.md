# 12 Acceptance Tests and Checklist

## Structural tests
- [ ] Current deployment backbone still exists and is unchanged where intentionally preserved.
- [ ] `String Alpha Localizer Feed` leaf deployment exists (if adopted).
- [ ] SET-A, Monitoring Site, Relay, and node leaf semantics are clear in metadata.
- [ ] Track SamplingFeature template/pattern is defined and usable.

## Metadata tests
- [ ] Every deployment has uid, name, description, purpose, and state.
- [ ] Every major system has plain-English explanation + source/provenance/docs.
- [ ] Every major procedure has method docs and version.
- [ ] Every important datastream has units, cadence, and product semantics.
- [ ] Existing repo image assets are referenced where appropriate.
- [ ] Generated SVG diagrams are attached/placed where appropriate.

## Schema tests
- [ ] Upgraded SENREP schema includes stable join/provenance fields.
- [ ] Localizer schema remains interpretable and quality-bearing.
- [ ] LOB schema remains explicit about uncertainty and classification.

## Runtime tests
- [ ] Simulator still produces LOBs.
- [ ] Localizer still produces location estimates.
- [ ] Click-to-report still creates SET SENREPs.
- [ ] Track identity remains stable by `contactId`.
- [ ] Reset/resilience logic still works.

## Explorer tests
- [ ] Deployments still render as the primary navigation backbone.
- [ ] Detection ranges, LOBs, localizer fixes, SENREPs, tracks, and observation trails remain coherent together.
- [ ] Richer metadata is visible in detail views or inspect workflows.

## Rollout checklist
- [ ] Current-state export taken
- [ ] Additive resource creation completed
- [ ] Metadata enrichment completed
- [ ] Runtime validation completed
- [ ] Explorer validation completed
- [ ] Old thin semantics documented or retired
