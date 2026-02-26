# What We're Building

Simple list of everything we need to create for the CSAPI client library.

---

## Main Component

**CSAPIEndpoint**
The thing developers import and use. Connects to servers, figures out what's available, lets you query and modify data.

---

## Service Discovery

**Conformance Reader**
Checks what features the server supports.

**Collections Reader**
Gets the list of available data collections and their details.

**URL Builder**
Constructs proper web addresses for fetching data, creating records, etc.

---

## Format Handlers

**GeoJSON Handler**
Reads and validates geographic data (points, lines, polygons, etc).

**SensorML Handler**
Reads sensor descriptions - what they are, what they measure, where they are.

**SWE Common Handler**
Reads observation data schemas and the actual measurements. Handles different data formats (JSON, CSV-style text, binary).

**Format Detector**
Figures out what format the server sent back.

**Validator**
Checks if data is correct and complete.

---

## Part 1 Resources

**Systems**
Sensors and sensor platforms - create, read, update, delete.

**Deployments**
Where and when sensors were placed - create, read, update, delete.

**Procedures**
How measurements are taken - create, read, update, delete.

**Sampling Features**
Locations where samples are collected - create, read, update, delete.

**Properties**
Things that can be measured (temperature, pressure, etc) - read only.

---

## Part 2 Resources

**DataStreams**
Ongoing series of observations from a sensor - create, read, update, delete.

**Observations**
Actual measurement data - create and read (lots of them at once if needed).

**Control Streams**
Command interfaces for controllable systems - create, read, update, delete.

**Commands**
Instructions sent to systems - create and read.

---

## Worker Support

**Background Processing**
Moves heavy data parsing off the main thread so web pages stay responsive.

---

## Tests

**Unit Tests**
Tests for each individual piece.

**Integration Tests**
Tests for complete workflows from start to finish.

**Performance Tests**
Makes sure large datasets process quickly enough.

**Test Data**
Real examples from actual servers to test against.

---

## Summary

- 1 main thing to use
- 3 discovery helpers
- 5 format handlers
- 9 resource managers
- 2 worker pieces
- Full test coverage

Everything needed for a complete CSAPI client.

This gives developers a complete, production-ready CSAPI client that works with any compliant server.

---

## Document Change Log

| Version | Date       | Changes                |
| ------- | ---------- | ---------------------- |
| 1.0     | 2026-02-01 | Initial component list |
