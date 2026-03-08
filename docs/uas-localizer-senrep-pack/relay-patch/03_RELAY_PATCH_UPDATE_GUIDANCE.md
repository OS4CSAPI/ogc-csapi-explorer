# Relay Patch — Update Guidance

## Apply this patch in the following order

### Step 1 — Confirm existing Relay resources
Verify the live branch already contains:
- Relay emplacement deployment
- Relay system resource

If yes:
- patch/enrich them in place

If no:
- create them using the included templates, then link them into the current deployment tree

### Step 2 — Enrich the Relay emplacement deployment
Add:
- name
- uid
- plain-English description
- deploymentType
- roleType
- purpose
- active/demo status
- occupant summary

### Step 3 — Enrich the Relay system
Add:
- name
- uid
- plain-English description
- systemKind
- roleType
- communications-support purpose
- ownership / maintainer metadata
- document/media links if available

### Step 4 — Add media/document references
If available, attach:
- vendor/reference page
- architecture/topology note
- photo/render of the relay hardware
- local branch topology diagram showing Relay placement

### Step 5 — Verify in Explorer
The Relay should now be inspectable as:
- a meaningful deployment leaf
- a meaningful system
- an understandable support element in the deployment-first view
