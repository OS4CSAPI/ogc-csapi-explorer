# 07 Resource-by-Resource Enrichment Matrix

| Resource | Structural role | Required enrichments | Recommended media/doc links |
|---|---|---|---|
| Orbital Tracking Demo | root deployment | name, uid, description, purpose, active/demo status | architecture diagram, overview doc |
| LEO Objects | grouping subdeployment | name, uid, description, grouping purpose | optional branch image |
| ISS Tracking Role | role subdeployment | name, uid, roleType, description, purpose | role/context image, Explorer screenshot |
| ISS Tracking — Position Feed | leaf deployment | name, uid, deploymentType=feed-leaf, purpose, occupant summary | optional point-fix explainer |
| ISS Tracking — Orbit Track Feed | leaf deployment | name, uid, deploymentType=feed-leaf, purpose, occupant summary | optional track explainer |
| iss-position-publisher | system | name, uid, description, sourceProvider, propagationModel, updateIntervalSec | NASA ISS image, NASA ISS page, architecture diagram |
| iss-orbittrack-publisher | system | name, uid, description, sourceProvider, propagationModel | orbit-track illustration, architecture diagram |
| sgp4-propagation:v1 | procedure | name, uid, version, inputs, outputs, assumptions, source docs | CelesTrak docs, method diagram |
| orbit-track-generation:v1 | procedure | name, uid, version, inputs, outputs, sampling/window semantics | orbit-track generation diagram |
| satPositionWGS84 | datastream | name, uid, description, units, cadence, quality/freshness semantics | schema explainer |
| orbitGroundTrack | datastream | name, uid, description, samplePeriodSec semantics, window semantics | example track thumbnail |
