# Relay Patch — Recommended Model

## Role of the Relay in the resource family
The Relay is not just miscellaneous support gear.

It should be modeled as a first-class support system whose purpose is to:
- maintain or extend communications reach,
- bridge remote sensing elements and monitoring/reporting elements,
- support the operational continuity of the sensor string / sensor net.

## Recommended modeling stance
### Keep
- the existing Relay emplacement in the deployment tree
- the Relay as its own system resource

### Enrich
- the Relay emplacement deployment metadata
- the Relay system metadata
- any communications/support-role documentation and media attachments

## Recommended structural semantics

### Deployment
**Relay Emplacement**
- category: deployment leaf
- roleType: communications-support
- deploymentType: support-leaf
- purpose: maintain relay capability between remote sensor assets and monitoring/reporting elements

### System
**Relay**
- systemKind: communications-relay
- roleType: relay-support
- purpose: relay / repeat / bridge sensor-network traffic as part of the deployed string/network architecture

## Why this matters
Without these semantics, the Relay looks like a nameless leftover support node.

With them, the Relay becomes:
- understandable to users,
- discoverable to clients,
- and clearly connected to the doctrinal arrangement of the network.
