# 11 Server Limitations and Workarounds

## Known OSH limitations from supplied source materials

### Scope leak
Per-datastream observation queries can return observations from all datastreams.
**Workaround:** always filter client-side by expected `datastream@id` and/or schema signature.

### `deployment@link` dropped on datastreams
Cannot rely on datastream -> deployment persistence.
**Workaround:** walk deployment tree to `platform@link` relationships instead.

### Control stream PUT catch-22
Control streams are effectively read-only after creation.
**Workaround:** treat them as create-once unless server behavior changes.

### Case-sensitive paths
Must use lowercase REST path segments such as `controlstreams`.

### REST datastream creation rejection
Datastream creation must follow the server-supported SWE/INSERT path rather than assuming generic REST creation will succeed.

### Conformance declaration gaps
Client behavior must be based on empirical probing, not just conformance-document assumptions.

## Known library/client limitations from supplied source materials

### OSHConnect-Python bugs
- `StreamableResource.__init__` patching required in some contexts
- `find_system()` UID matching unreliable
- `resource_id` not always populated

### Complex nested types
UI parsing for DataArray / complex nested types is incomplete in some places.
**Workaround:** allow raw JSON fallback and/or explicit custom rendering.

## Design consequence for this pack
All templates and recommendations should be read as:
- semantically preferred,
- but implemented with current server realities in mind.
