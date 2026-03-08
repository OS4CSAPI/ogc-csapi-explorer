# 08 Resource-by-Resource Enrichment Matrix

| Resource | Category | Keep / Add | Required enrichments | Recommended media/docs |
|---|---|---|---|---|
| ICO | deployment | keep | uid, name, description, purpose, state | optional branch context diagram |
| RSO | deployment | keep | uid, name, purpose, echelon role | optional doctrine note |
| SSO | deployment | keep | uid, name, purpose, echelon role | optional surveillance-plan diagram |
| SNET | deployment | keep | uid, name, network purpose | topology diagram |
| Sensor Field 001 | deployment | keep | uid, name, field purpose | field sketch if available |
| String Alpha | deployment | keep/enrich | uid, name, purpose, string role | string surveillance diagram |
| Node 1/2/3 Emplacements | deployment | keep/enrich | uid, name, leaf semantics, occupant summary | node placement image if available |
| SET-A Emplacement | deployment | keep/enrich | uid, leaf semantics, reporting role | reporting-role diagram |
| Monitoring Site Emplacement | deployment | keep/enrich | uid, purpose, reporting/dissemination role | monitoring-site diagram |
| Relay Emplacement | deployment | keep/enrich | uid, relay role | relay concept image |
| String Alpha Localizer Feed | deployment | add | uid, leaf semantics, fusion role | fusion architecture diagram |
| AZ-MA-1 / 2 / 3 | system | keep/enrich | identity, vendor, role, provenance, photos/docs | XMOS photo, vendor page |
| SET-A | system | keep/enrich | team role, reporting authority, owner, state | SENREP/reporting diagram |
| Monitoring Site | system | keep/enrich | monitoring role, reporting responsibilities, redundancy role | monitoring-site diagram |
| Relay | system | keep/enrich | relay purpose, support role | relay diagram |
| AZ String Alpha Localizer | system | keep/enrich | producer description, fusion role, method refs | WLS/localizer diagram |
| lob-wls-triangulation:v1 | procedure | keep/enrich | version, inputs, outputs, assumptions | bearing-intersection method note |
| senrep:sop:v1 | procedure | add/enrich | version, doctrinal purpose, inputs/outputs | SENREP process diagram |
| az_string_alpha_location_estimate | datastream | keep/enrich | units, product type, quality semantics | gold-dot / CEP explainer |
| senrep | datastream | upgrade | richer schema, provenance/join semantics | SENREP field map |
| az_ma_n_lob | datastream | keep/enrich | units, uncertainty semantics | bearing-line illustration |
| Track SamplingFeature | sampling feature | add/template | uid, contactId, lifecycle state | optional symbol/track icon |
