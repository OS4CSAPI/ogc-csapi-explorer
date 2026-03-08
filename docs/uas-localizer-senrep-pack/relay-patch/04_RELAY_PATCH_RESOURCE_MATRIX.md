# Relay Patch — Resource Matrix Entries

| Resource | Category | Keep / Add | Required enrichments | Recommended media/docs |
|---|---|---|---|---|
| Relay Emplacement | deployment | keep/enrich | uid, name, description, deploymentType, roleType, purpose, active/demo state, occupant summary | topology diagram, relay concept image |
| Relay | system | keep/enrich | uid, name, description, systemKind, roleType, purpose, owner/maintainer, state | vendor page, hardware photo, support-role note |

## Recommended values

### Relay Emplacement
- `deploymentType`: `support-leaf`
- `roleType`: `communications-support`

### Relay
- `systemKind`: `communications-relay`
- `roleType`: `relay-support`
