# Relay Patch — Structural / Semantic Diff

## What was missing
In the earlier pack, Relay was mentioned in the deployment backbone and resource matrix planning discussion,
but it did not get the same concrete implementation-ready treatment as the Localizer or SET.

That means the Relay lacked:
- its own focused guidance
- relay-specific enrichment recommendations
- ready-to-use JSON templates

## What this patch adds
### 1) Relay emplacement semantics
Adds explicit metadata guidance so the Relay emplacement is clearly identified as:
- a deployment leaf
- a communications-support role
- a support node in the operational architecture

### 2) Relay system semantics
Adds explicit metadata guidance so the Relay system is clearly identified as:
- a communications relay / repeater / bridge system
- part of the deployed sensor-network support chain
- owned/maintained within the branch like the other first-class systems

### 3) Relay implementation templates
Adds JSON templates for:
- Relay system enrichment
- Relay emplacement deployment enrichment

## What this patch does not do
It does not invent unverified hardware-specific details.
Those should only be filled in if you have:
- a relay export/backup
- a vendor/model reference
- a photo/reference page
