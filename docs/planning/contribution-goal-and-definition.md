# Contribution Goal and Definition

**Version:** 1.1  
**Date:** February 13, 2026

---

## Contribution Goal

Enable developers to interact with sensor networks, observation data, and system control through the Camptocamp OGC Client Library using the same unified interface they already use for other OGC APIs.

Deliver a production-ready, specification-complete Connected Systems API (CSAPI) implementation that fills a critical ecosystem gap by providing comprehensive TypeScript support for sensor system discovery, observation data retrieval, and remote system command and control capabilities.

---

## Contribution Definition

Complete implementation of OGC API - Connected Systems Parts 1 & 2 standards for the Camptocamp OGC Client Library, consisting of:

**Core Integration**

- Single QueryBuilder class with 80 methods covering all 9 CSAPI resource types (Systems, Deployments, Procedures, Sampling Features, Properties, DataStreams, Observations, Control Streams, Commands)
- Factory method integration pattern following established library architecture (EDR pattern)
- Resource validation in all methods with fail-fast error handling
- Complete query parameter support (spatial, temporal, hierarchical, relationship-based, property-based filters)
- Both pagination modes (offset-based and cursor-based)

**Format Support**

- SensorML 3.0 parser with complete type system for all system models and recursive component parsing
- SWE Common 3.0 parser supporting all three encodings (JSON, Text/CSV, Binary) with schema validation
- GeoJSON extensions recognizing all CSAPI-specific resource types and properties
- Format detection and content negotiation for all CSAPI media types

**Quality Standards**

- Full TypeScript type safety with three-tier type hierarchy (1,750-2,400 lines of interfaces)
- > 80% test coverage with comprehensive unit and integration tests
- JSDoc documentation for all public APIs
- Compliance with OGC API - Connected Systems specifications (Parts 1 & 2)
- Zero-breaking-change integration with existing library functionality

**Deliverables**

- 24 implementation files (~4,614-6,094 lines)
- 22 test files (~4,040-5,340 lines)
- Complete API documentation
- Implementation conforming to all upstream library patterns and conventions
