# Relay-Only Patch Pack

This is a targeted patch pack to fill the missing **Relay** portion of the
UAS / Localizer / SENREP implementation-ready pack.

## What this patch adds
- relay-specific structural and metadata guidance
- relay-specific update notes for the existing deployment-first branch
- relay-specific enrichment matrix entries
- implementation-ready JSON templates for:
  - Relay system enrichment
  - Relay emplacement deployment enrichment

## Intended use
Apply this patch on top of the larger UAS / Localizer / SENREP pack rather than
rebuilding that whole pack.

## Scope
This patch assumes:
- the current deployment backbone remains authoritative
- the Relay already exists conceptually in the branch
- the main missing work is semantic/metadata completion for the Relay resource family slice

## Limitation
This patch does **not** assume a fully verified vendor/model-specific relay backup artifact.
Where rich hardware-specific details are unknown, placeholders are left for:
- manufacturer
- model
- serial / asset tag
- photo / reference page
