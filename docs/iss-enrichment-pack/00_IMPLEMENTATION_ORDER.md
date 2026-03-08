# 00 Implementation Order

## Build sequence
1. Confirm current-state inventory and backup/export what exists.
2. Create the new deployment tree.
3. Create the two producer systems.
4. Create the two procedures.
5. Create the two datastreams and validate schema round-trip.
6. Update publisher discovery to use stable names/UIDs.
7. Start publishing position fixes.
8. Start publishing orbit-track products.
9. Enrich deployments/systems/procedures/datastreams with descriptive metadata and linked media.
10. Verify Explorer rendering and deployed-system navigation.
11. Only then consider retiring or aliasing the older flat ISS branch.

## Why this order
- It preserves rollback.
- It allows additive migration.
- It avoids trying to enrich metadata on the wrong structure.
- It ensures the deployment backbone exists before the producer family depends on it.
