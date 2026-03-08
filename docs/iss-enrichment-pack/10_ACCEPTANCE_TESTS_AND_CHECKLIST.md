# 10 Acceptance Tests and Checklist

## Structural acceptance tests
- [ ] Deployment tree exists exactly as planned.
- [ ] Position feed leaf exists and resolves to position publisher system.
- [ ] Orbit-track feed leaf exists and resolves to orbit-track publisher system.
- [ ] Position and orbit-track datastreams are separate resources.
- [ ] SGP4 and orbit-track procedures are separate resources.

## Metadata acceptance tests
- [ ] Every deployment has name, uid, description, purpose.
- [ ] Every system has source/provider metadata and a plain-English description.
- [ ] Every procedure has version, inputs, outputs, and method notes.
- [ ] Every datastream has units, cadence, and product semantics.
- [ ] Every major resource has at least one linked document/reference where appropriate.
- [ ] ISS image/reference placement is present on the relevant system resource(s).

## Publisher acceptance tests
- [ ] Publisher discovers target resources by UID/name, not hardcoded ID.
- [ ] Position publishing works after clean restart.
- [ ] Orbit-track publishing works after clean restart.
- [ ] Publisher survives temporary source/network/server interruption.

## Explorer acceptance tests
- [ ] ISS appears in deployment-first navigation.
- [ ] Current position renders correctly.
- [ ] Orbit track renders correctly.
- [ ] Observation-derived trail still behaves correctly if enabled.
- [ ] Resource detail views visibly expose the richer metadata.

## Rollout checklist
- [ ] Current-state export taken
- [ ] New resources created additively
- [ ] Publisher updated
- [ ] Explorer verified
- [ ] Old flat branch retired or documented
