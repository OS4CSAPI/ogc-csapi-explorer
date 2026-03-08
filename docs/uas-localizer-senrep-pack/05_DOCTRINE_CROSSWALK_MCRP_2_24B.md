# 05 Doctrine Crosswalk — MCRP 2-24B (Attached Version)

This file uses the **attached MCRP 2-24B Remote Sensor Operations PDF version** as the doctrinal reference.

## Key doctrinal definitions reflected in the model

### Remote sensor system
The manual defines the remote sensor system as an equipment suite of sensors,
communications data-relay devices, and monitoring equipment.

### Sensor string
A sensor string is a grouping of 2 or more (usually 3–5) remote sensors in the same area,
used to cover a specific surveillance target.

### Sensor network / net
A sensor net is an integrated system of strings, relays, and monitoring sites established
to provide surveillance over all or part of the area of operations.

### Monitoring site
A monitoring site consists of monitoring equipment, communications equipment, and one or
more sensor operators. Monitoring sites are located to maintain communications line-of-sight
with sensors/relays and should be positioned to facilitate rapid reporting.

### SET
The doctrine describes the Sensor Employment Team (SET) as the basic unit of remote sensor
employment and the smallest element capable of independent employment.

### SENREP
The doctrine identifies the Sensor Report (SENREP) as the standard format used to report
sensor data, alongside Sensor Status Reports and JRSR/R reports.

## How the current/target model aligns

| Doctrine concept | Current/target CSAPI modeling |
|---|---|
| Sensor string | `String Alpha` deployment |
| Sensor network | SNET + Field + String hierarchy |
| Monitoring site | Monitoring Site system + emplacement deployment |
| SET | SET-A system + emplacement deployment + SENREP owner |
| Sensor reports | SET-owned SENREP datastream |
| Sensor net operations | Simulator/localizer/reporting workflow plus deployment hierarchy |

## Doctrine-informed design consequences
1. Keep `String Alpha` as a real deployment-level object.
2. Keep SET as a first-class system/deployment, not just an attribute.
3. Keep Monitoring Site as a first-class system/deployment.
4. Treat reporting timeliness and monitoring redundancy as metadata-worthy concepts.
5. Preserve distinction between:
   - raw detection
   - monitoring/analysis
   - reporting/dissemination

## Practical doctrine-to-resource mapping
- raw node sensing -> MA node systems and their datastreams
- integrated string-level inference -> localizer system and location-estimate datastream
- operator/team reporting -> SET-A system and SENREP datastream
- operational arrangement -> deployment hierarchy

## Recommendation
The doctrine strongly supports the deployment backbone you already built.
The next improvement is not to flatten it, but to enrich it and finish the reporting/identity semantics around SET/localizer/track creation.
