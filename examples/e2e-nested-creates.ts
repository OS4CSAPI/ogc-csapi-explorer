/**
 * End-to-End Nested Create Operations Test
 *
 * Follow-up to e2e-write-operations.ts — the initial test found that
 * `createDataStream()` POSTs to `/datastreams` (top-level) which the OSH
 * SensorHub rejects with 405: "Datastreams can only be created within a
 * System resource". This test validates the nested creation pattern:
 *
 *   System → Datastream (under system) → Observation (under datastream)
 *
 * It also tests whether `getSystemDataStreams(id)` can serve as the POST
 * target (workaround for missing `createDataStreamForSystem(id)` method).
 *
 * Usage:
 *   npx tsx examples/e2e-nested-creates.ts
 */

import CSAPIQueryBuilder from '../src/ogc-api/csapi/url_builder.js';
import { scanCsapiLinks } from '../src/ogc-api/csapi/helpers.js';
import { parseCollectionResponse } from '../src/ogc-api/csapi/formats/response.js';
import { extractCSAPIFeature, getCSAPIResourceType } from '../src/ogc-api/csapi/formats/geojson.js';
import type { OgcApiCollectionInfo } from '../src/ogc-api/model.js';

// ========================================
// Configuration
// ========================================

const BASE_URL = 'http://45.55.99.236:8080/sensorhub/api';
const AUTH = 'Basic ' + Buffer.from('admin:admin').toString('base64');
const NOW = new Date().toISOString();
const UNIQUE = Date.now();

// ========================================
// HTTP Helper
// ========================================

interface HttpResult {
  status: number;
  statusText: string;
  headers: Record<string, string>;
  body: any;
  url: string;
  method: string;
}

async function httpRequest(
  method: string,
  url: string,
  body?: object,
  contentType?: string
): Promise<HttpResult> {
  const fullUrl = url.startsWith('http') ? url : `${BASE_URL}${url}`;
  const headers: Record<string, string> = {
    Authorization: AUTH,
    Accept: 'application/json',
  };
  if (body && contentType) {
    headers['Content-Type'] = contentType;
  }

  const response = await fetch(fullUrl, {
    method,
    headers,
    body: body ? JSON.stringify(body) : undefined,
  });

  let responseBody: any;
  const text = await response.text();
  try {
    responseBody = JSON.parse(text);
  } catch {
    responseBody = text;
  }

  const responseHeaders: Record<string, string> = {};
  response.headers.forEach((value, key) => {
    responseHeaders[key] = value;
  });

  return {
    status: response.status,
    statusText: response.statusText,
    headers: responseHeaders,
    body: responseBody,
    url: fullUrl,
    method,
  };
}

// ========================================
// Result Tracking
// ========================================

interface TestResult {
  name: string;
  passed: boolean;
  builderMethod: string;
  generatedUrl: string;
  httpMethod: string;
  httpStatus: number;
  details: string;
  serverResponse?: any;
  error?: string;
  finding?: string;
}

const results: TestResult[] = [];

function extractId(result: HttpResult): string | null {
  const loc = result.headers['location'] || '';
  const parts = loc.split('/');
  return parts[parts.length - 1] || null;
}

function pct(s: string) { return `\x1b[32m✓\x1b[0m ${s}`; }  // green check
function pfl(s: string) { return `\x1b[31m✗\x1b[0m ${s}`; }  // red x
function pwn(s: string) { return `\x1b[33m⚠\x1b[0m ${s}`; }  // yellow warning

// ========================================
// Main Test
// ========================================

async function main() {
  const hr = '═'.repeat(60);

  console.log('╔' + '═'.repeat(60) + '╗');
  console.log('║    CSAPIQueryBuilder — Nested Create Operations Test     ║');
  console.log('╠' + '═'.repeat(60) + '╣');
  console.log(`║ Target: ${BASE_URL}`.padEnd(61) + '║');
  console.log(`║ Date:   ${NOW}`.padEnd(61) + '║');
  console.log('╚' + '═'.repeat(60) + '╝');

  // ── SETUP: Create builder ──
  console.log('\n=== Setting Up CSAPIQueryBuilder ===\n');

  const landing = await httpRequest('GET', '/');
  console.log(`Landing page: ${landing.status} OK`);

  const links = landing.body.links || [];
  const csapiLinks = scanCsapiLinks(links);
  console.log(`scanCsapiLinks found: ${csapiLinks.size} resource types`);

  // Convert absolute → relative
  const resourceUrls = new Map<string, string>();
  for (const [type, href] of csapiLinks) {
    const url = new URL(href);
    resourceUrls.set(type, url.pathname.replace('/sensorhub/api', ''));
    console.log(`  ${type} → ${href}`);
  }

  // Build synthetic collection with self link and resource links
  const syntheticLinks = Array.from(resourceUrls).map(([type, url]) => ({
    rel: type,
    href: url,
  }));
  syntheticLinks.push({ rel: 'self', href: '/' });

  const syntheticCollection = {
    id: 'nested-test',
    title: 'OSH SensorHub',
    links: syntheticLinks,
  } as OgcApiCollectionInfo;

  const builder = new CSAPIQueryBuilder(syntheticCollection, resourceUrls);
  console.log(`\nBuilder created. Available: [${[...builder.availableResources].join(', ')}]\n`);

  // ── Track created IDs for cleanup ──
  const cleanup: { type: string; id: string; url: string }[] = [];

  // ═══════════════════════════════════════════════════
  //  PHASE 1: CREATE A PARENT SYSTEM
  // ═══════════════════════════════════════════════════
  console.log(hr);
  console.log('  PHASE 1: CREATE PARENT SYSTEM');
  console.log(hr + '\n');

  const systemPayload = {
    type: 'Feature',
    properties: {
      uid: `urn:csapi-explorer:nested-test:system:${UNIQUE}`,
      featureType: 'http://www.w3.org/ns/sosa/Platform',
      name: 'Nested Test System — CSAPI Explorer',
      description: 'Parent system for nested-create testing.',
      validTime: [NOW, 'now'],
    },
  };

  const createSystemUrl = builder.createSystem();
  const systemResult = await httpRequest('POST', createSystemUrl, systemPayload, 'application/geo+json');
  const systemId = extractId(systemResult);

  if (systemResult.status === 201 && systemId) {
    console.log(pct(`CREATE System → ${createSystemUrl}`));
    console.log(`   HTTP: POST ${systemResult.status} — ID: ${systemId}`);
    cleanup.push({ type: 'system', id: systemId, url: builder.deleteSystem(systemId) });
    results.push({
      name: 'CREATE parent System',
      passed: true,
      builderMethod: 'builder.createSystem()',
      generatedUrl: createSystemUrl,
      httpMethod: `POST ${systemResult.status}`,
      httpStatus: systemResult.status,
      details: `Created system ${systemId}`,
    });
  } else {
    console.log(pfl(`CREATE System FAILED: ${systemResult.status} ${systemResult.statusText}`));
    console.log(`   Response: ${JSON.stringify(systemResult.body)}`);
    results.push({
      name: 'CREATE parent System',
      passed: false,
      builderMethod: 'builder.createSystem()',
      generatedUrl: createSystemUrl,
      httpMethod: `POST ${systemResult.status}`,
      httpStatus: systemResult.status,
      details: `Failed: ${systemResult.status}`,
      error: JSON.stringify(systemResult.body),
    });
    console.log('\nCannot continue without a parent system. Aborting.');
    await writeResults();
    return;
  }

  // ═══════════════════════════════════════════════════
  //  PHASE 2: CREATE DATASTREAM UNDER SYSTEM (NESTED)
  // ═══════════════════════════════════════════════════
  console.log('\n' + hr);
  console.log('  PHASE 2: NESTED DATASTREAM CREATION');
  console.log(hr + '\n');

  // 2a: First confirm top-level createDataStream() fails (expected)
  console.log('--- Test 2a: Top-level createDataStream() (expected 405) ---\n');
  const topLevelDsUrl = builder.createDataStream();
  const topLevelDsPayload = {
    name: 'Test DataStream — top-level',
    outputName: 'testTopLevel',
    schema: {
      obsFormat: 'application/json',
      recordSchema: {
        type: 'DataRecord',
        label: 'Test Record',
        fields: [
          { type: 'Time', name: 'time', label: 'Timestamp', definition: 'http://www.opengis.net/def/property/OGC/0/SamplingTime', referenceFrame: 'http://www.opengis.net/def/trs/BIPM/0/UTC', uom: { href: 'http://www.opengis.net/def/uom/ISO-8601/0/Gregorian' } },
          { type: 'Quantity', name: 'temperature', label: 'Temperature', definition: 'http://qudt.org/vocab/quantitykind/Temperature', uom: { code: 'Cel' } },
        ],
      },
    },
  };

  const topLevelDsResult = await httpRequest('POST', topLevelDsUrl, topLevelDsPayload, 'application/json');
  if (topLevelDsResult.status === 405) {
    console.log(pct(`Top-level createDataStream() correctly rejected with 405`));
    console.log(`   URL: ${topLevelDsUrl}`);
    console.log(`   Server: ${JSON.stringify(topLevelDsResult.body)}`);
    results.push({
      name: 'Top-level createDataStream() — expected 405',
      passed: true,
      builderMethod: 'builder.createDataStream()',
      generatedUrl: topLevelDsUrl,
      httpMethod: `POST ${topLevelDsResult.status}`,
      httpStatus: topLevelDsResult.status,
      details: 'Correctly rejected: 405 Method Not Allowed',
      finding: 'FINDING: createDataStream() generates top-level URL that servers reject. Datastreams must be created as nested resources under a system.',
    });
  } else {
    console.log(pwn(`Top-level createDataStream() got ${topLevelDsResult.status} (expected 405)`));
    results.push({
      name: 'Top-level createDataStream() — expected 405',
      passed: false,
      builderMethod: 'builder.createDataStream()',
      generatedUrl: topLevelDsUrl,
      httpMethod: `POST ${topLevelDsResult.status}`,
      httpStatus: topLevelDsResult.status,
      details: `Unexpected status ${topLevelDsResult.status} (expected 405)`,
    });
  }

  // 2b: Use getSystemDataStreams(systemId) as POST target (workaround)
  console.log('\n--- Test 2b: Nested create via getSystemDataStreams(systemId) ---\n');
  const nestedDsUrl = builder.getSystemDataStreams(systemId);
  const datastreamPayload = {
    name: `Test DataStream — nested under ${systemId}`,
    outputName: `testNested_${UNIQUE}`,
    schema: {
      obsFormat: 'application/json',
      recordSchema: {
        type: 'DataRecord',
        label: 'E2E Nested Test Record',
        fields: [
          { type: 'Time', name: 'time', label: 'Timestamp', definition: 'http://www.opengis.net/def/property/OGC/0/SamplingTime', referenceFrame: 'http://www.opengis.net/def/trs/BIPM/0/UTC', uom: { href: 'http://www.opengis.net/def/uom/ISO-8601/0/Gregorian' } },
          { type: 'Quantity', name: 'temperature', label: 'Temperature', definition: 'http://qudt.org/vocab/quantitykind/Temperature', uom: { code: 'Cel' } },
        ],
      },
    },
  };

  const nestedDsResult = await httpRequest('POST', nestedDsUrl, datastreamPayload, 'application/json');
  const datastreamId = extractId(nestedDsResult);

  if (nestedDsResult.status === 201 && datastreamId) {
    console.log(pct(`Nested datastream created via getSystemDataStreams()`));
    console.log(`   Builder: builder.getSystemDataStreams('${systemId}') → "${nestedDsUrl}"`);
    console.log(`   HTTP: POST ${nestedDsResult.status} — ID: ${datastreamId}`);
    cleanup.push({ type: 'datastream', id: datastreamId, url: builder.deleteDataStream(datastreamId) });
    results.push({
      name: 'CREATE Datastream (nested under system)',
      passed: true,
      builderMethod: `builder.getSystemDataStreams('${systemId}')`,
      generatedUrl: nestedDsUrl,
      httpMethod: `POST ${nestedDsResult.status}`,
      httpStatus: nestedDsResult.status,
      details: `Created datastream ${datastreamId} under system ${systemId}`,
      finding: 'WORKAROUND: getSystemDataStreams(id) can serve as POST target for nested datastream creation. Library should add createDataStreamForSystem(systemId) method.',
    });
  } else {
    console.log(pfl(`Nested datastream creation FAILED: ${nestedDsResult.status}`));
    console.log(`   URL: ${nestedDsUrl}`);
    console.log(`   Response: ${JSON.stringify(nestedDsResult.body)}`);
    results.push({
      name: 'CREATE Datastream (nested under system)',
      passed: false,
      builderMethod: `builder.getSystemDataStreams('${systemId}')`,
      generatedUrl: nestedDsUrl,
      httpMethod: `POST ${nestedDsResult.status}`,
      httpStatus: nestedDsResult.status,
      details: `Failed: ${nestedDsResult.status}`,
      serverResponse: nestedDsResult.body,
      error: JSON.stringify(nestedDsResult.body),
    });
  }

  // 2c: Verify created datastream with GET
  console.log('\n--- Test 2c: Verify nested datastream with GET ---\n');
  if (datastreamId) {
    const getDsUrl = builder.getDataStream(datastreamId);
    const getDsResult = await httpRequest('GET', getDsUrl);
    if (getDsResult.status === 200) {
      console.log(pct(`GET nested datastream ${datastreamId}`));
      console.log(`   Builder: builder.getDataStream('${datastreamId}') → "${getDsUrl}"`);
      console.log(`   Name: ${getDsResult.body?.name}`);
      results.push({
        name: 'GET nested Datastream (verify creation)',
        passed: true,
        builderMethod: `builder.getDataStream('${datastreamId}')`,
        generatedUrl: getDsUrl,
        httpMethod: `GET ${getDsResult.status}`,
        httpStatus: getDsResult.status,
        details: `Retrieved: ${getDsResult.body?.name}`,
        serverResponse: getDsResult.body,
      });
    } else {
      console.log(pfl(`GET nested datastream FAILED: ${getDsResult.status}`));
      results.push({
        name: 'GET nested Datastream (verify creation)',
        passed: false,
        builderMethod: `builder.getDataStream('${datastreamId}')`,
        generatedUrl: getDsUrl,
        httpMethod: `GET ${getDsResult.status}`,
        httpStatus: getDsResult.status,
        details: `Failed: ${getDsResult.status}`,
      });
    }
  } else {
    console.log('   Skipped (no datastream ID)');
  }

  // 2d: List system's datastreams to verify nesting
  console.log('\n--- Test 2d: List system datastreams to verify relationship ---\n');
  if (datastreamId) {
    const listDsUrl = builder.getSystemDataStreams(systemId);
    const listDsResult = await httpRequest('GET', listDsUrl);
    if (listDsResult.status === 200) {
      const items = listDsResult.body?.items || [];
      const found = items.find((i: any) => i.id === datastreamId);
      console.log(pct(`List system datastreams shows ${items.length} items`));
      console.log(`   Builder: builder.getSystemDataStreams('${systemId}') → "${listDsUrl}"`);
      console.log(`   Our datastream found in list: ${found ? 'Yes' : 'No'}`);
      results.push({
        name: 'LIST system datastreams (verify nesting)',
        passed: !!found,
        builderMethod: `builder.getSystemDataStreams('${systemId}')`,
        generatedUrl: listDsUrl,
        httpMethod: `GET ${listDsResult.status}`,
        httpStatus: listDsResult.status,
        details: `${items.length} items, our datastream ${found ? 'found' : 'NOT found'}`,
      });
    } else {
      console.log(pfl(`List system datastreams FAILED: ${listDsResult.status}`));
      results.push({
        name: 'LIST system datastreams (verify nesting)',
        passed: false,
        builderMethod: `builder.getSystemDataStreams('${systemId}')`,
        generatedUrl: listDsUrl,
        httpMethod: `GET ${listDsResult.status}`,
        httpStatus: listDsResult.status,
        details: `Failed: ${listDsResult.status}`,
      });
    }
  }

  // ═══════════════════════════════════════════════════
  //  PHASE 3: CREATE OBSERVATION UNDER DATASTREAM
  // ═══════════════════════════════════════════════════
  console.log('\n' + hr);
  console.log('  PHASE 3: NESTED OBSERVATION CREATION');
  console.log(hr + '\n');

  let observationId: string | null = null;
  if (datastreamId) {
    // 3a: Create observation using library's createObservation(datastreamId)
    console.log('--- Test 3a: createObservation(datastreamId) ---\n');
    const createObsUrl = builder.createObservation(datastreamId);
    const observationPayload = {
      phenomenonTime: NOW,
      resultTime: NOW,
      result: {
        time: NOW,
        temperature: 23.5,
      },
    };

    const createObsResult = await httpRequest('POST', createObsUrl, observationPayload, 'application/json');
    observationId = extractId(createObsResult);

    if (createObsResult.status === 201 && observationId) {
      console.log(pct(`CREATE Observation via createObservation()`));
      console.log(`   Builder: builder.createObservation('${datastreamId}') → "${createObsUrl}"`);
      console.log(`   HTTP: POST ${createObsResult.status} — ID: ${observationId}`);
      results.push({
        name: 'CREATE Observation (nested under datastream)',
        passed: true,
        builderMethod: `builder.createObservation('${datastreamId}')`,
        generatedUrl: createObsUrl,
        httpMethod: `POST ${createObsResult.status}`,
        httpStatus: createObsResult.status,
        details: `Created observation ${observationId} under datastream ${datastreamId}`,
      });
    } else {
      console.log(pfl(`CREATE Observation FAILED: ${createObsResult.status}`));
      console.log(`   URL: ${createObsUrl}`);
      console.log(`   Response: ${JSON.stringify(createObsResult.body)}`);
      results.push({
        name: 'CREATE Observation (nested under datastream)',
        passed: false,
        builderMethod: `builder.createObservation('${datastreamId}')`,
        generatedUrl: createObsUrl,
        httpMethod: `POST ${createObsResult.status}`,
        httpStatus: createObsResult.status,
        details: `Failed: ${createObsResult.status}`,
        serverResponse: createObsResult.body,
        error: JSON.stringify(createObsResult.body),
      });
    }

    // 3b: Verify observation with GET
    console.log('\n--- Test 3b: GET Observation by ID ---\n');
    if (observationId) {
      const getObsUrl = builder.getObservation(observationId);
      const getObsResult = await httpRequest('GET', getObsUrl);
      if (getObsResult.status === 200) {
        console.log(pct(`GET Observation ${observationId}`));
        console.log(`   Builder: builder.getObservation('${observationId}') → "${getObsUrl}"`);
        console.log(`   Result: ${JSON.stringify(getObsResult.body?.result)}`);
        results.push({
          name: 'GET Observation (verify creation)',
          passed: true,
          builderMethod: `builder.getObservation('${observationId}')`,
          generatedUrl: getObsUrl,
          httpMethod: `GET ${getObsResult.status}`,
          httpStatus: getObsResult.status,
          details: `Retrieved observation with result: ${JSON.stringify(getObsResult.body?.result)}`,
          serverResponse: getObsResult.body,
        });
      } else {
        console.log(pfl(`GET Observation FAILED: ${getObsResult.status}`));
        results.push({
          name: 'GET Observation (verify creation)',
          passed: false,
          builderMethod: `builder.getObservation('${observationId}')`,
          generatedUrl: getObsUrl,
          httpMethod: `GET ${getObsResult.status}`,
          httpStatus: getObsResult.status,
          details: `Failed: ${getObsResult.status}`,
        });
      }
    }

    // 3c: List datastream's observations to verify nesting
    console.log('\n--- Test 3c: List datastream observations ---\n');
    const listObsUrl = builder.getObservationsForDatastream(datastreamId);
    const listObsResult = await httpRequest('GET', listObsUrl);
    if (listObsResult.status === 200) {
      const items = listObsResult.body?.items || [];
      console.log(pct(`List datastream observations: ${items.length} items`));
      console.log(`   Builder: builder.getObservationsForDatastream('${datastreamId}') → "${listObsUrl}"`);
      results.push({
        name: 'LIST observations for datastream',
        passed: items.length > 0,
        builderMethod: `builder.getObservationsForDatastream('${datastreamId}')`,
        generatedUrl: listObsUrl,
        httpMethod: `GET ${listObsResult.status}`,
        httpStatus: listObsResult.status,
        details: `${items.length} observations found`,
      });
    } else {
      console.log(pfl(`List datastream observations FAILED: ${listObsResult.status}`));
      results.push({
        name: 'LIST observations for datastream',
        passed: false,
        builderMethod: `builder.getObservationsForDatastream('${datastreamId}')`,
        generatedUrl: listObsUrl,
        httpMethod: `GET ${listObsResult.status}`,
        httpStatus: listObsResult.status,
        details: `Failed: ${listObsResult.status}`,
      });
    }
  } else {
    console.log('   Skipped — no datastream to attach observation to');
  }

  // ═══════════════════════════════════════════════════
  //  PHASE 4: UPDATE & DELETE NESTED RESOURCES
  // ═══════════════════════════════════════════════════
  console.log('\n' + hr);
  console.log('  PHASE 4: UPDATE & DELETE NESTED RESOURCES');
  console.log(hr + '\n');

  // 4a: Update datastream
  if (datastreamId) {
    console.log('--- Test 4a: UPDATE Datastream (PUT) ---\n');
    const updateDsUrl = builder.updateDataStream(datastreamId);
    const updateDsPayload = {
      ...datastreamPayload,
      name: `Test DataStream — UPDATED — nested under ${systemId}`,
    };
    const updateDsResult = await httpRequest('PUT', updateDsUrl, updateDsPayload, 'application/json');
    if (updateDsResult.status === 204) {
      console.log(pct(`UPDATE Datastream ${datastreamId}`));
      console.log(`   Builder: builder.updateDataStream('${datastreamId}') → "${updateDsUrl}"`);
      results.push({
        name: 'UPDATE Datastream (PUT)',
        passed: true,
        builderMethod: `builder.updateDataStream('${datastreamId}')`,
        generatedUrl: updateDsUrl,
        httpMethod: `PUT ${updateDsResult.status}`,
        httpStatus: updateDsResult.status,
        details: 'Updated successfully (204)',
      });

      // Verify update
      const verifyDs = await httpRequest('GET', builder.getDataStream(datastreamId));
      console.log(`   Verification: name = "${verifyDs.body?.name}"`);
      console.log(`   Update verified: ${verifyDs.body?.name?.includes('UPDATED') ? '✓' : '✗'}`);
    } else {
      console.log(pfl(`UPDATE Datastream FAILED: ${updateDsResult.status}`));
      console.log(`   Response: ${JSON.stringify(updateDsResult.body)}`);
      results.push({
        name: 'UPDATE Datastream (PUT)',
        passed: false,
        builderMethod: `builder.updateDataStream('${datastreamId}')`,
        generatedUrl: updateDsUrl,
        httpMethod: `PUT ${updateDsResult.status}`,
        httpStatus: updateDsResult.status,
        details: `Failed: ${updateDsResult.status}`,
        serverResponse: updateDsResult.body,
      });
    }
  }

  // 4b: Delete observation
  if (observationId) {
    console.log('\n--- Test 4b: DELETE Observation ---\n');
    const deleteObsUrl = builder.deleteObservation(observationId);
    const deleteObsResult = await httpRequest('DELETE', deleteObsUrl);
    if (deleteObsResult.status === 204) {
      console.log(pct(`DELETE Observation ${observationId}`));
      console.log(`   Builder: builder.deleteObservation('${observationId}') → "${deleteObsUrl}"`);

      // Verify deletion
      const verifyObs = await httpRequest('GET', builder.getObservation(observationId));
      console.log(`   Verification GET: ${verifyObs.status} (expected 404)`);
      console.log(`   Delete verified: ${verifyObs.status === 404 ? '✓' : '✗'}`);
      results.push({
        name: 'DELETE Observation',
        passed: true,
        builderMethod: `builder.deleteObservation('${observationId}')`,
        generatedUrl: deleteObsUrl,
        httpMethod: `DELETE ${deleteObsResult.status}`,
        httpStatus: deleteObsResult.status,
        details: `Deleted, verification GET: ${verifyObs.status}`,
      });
    } else {
      console.log(pfl(`DELETE Observation FAILED: ${deleteObsResult.status}`));
      results.push({
        name: 'DELETE Observation',
        passed: false,
        builderMethod: `builder.deleteObservation('${observationId}')`,
        generatedUrl: deleteObsUrl,
        httpMethod: `DELETE ${deleteObsResult.status}`,
        httpStatus: deleteObsResult.status,
        details: `Failed: ${deleteObsResult.status}`,
      });
    }
  }

  // 4c: Delete datastream
  if (datastreamId) {
    console.log('\n--- Test 4c: DELETE Datastream ---\n');
    const deleteDsUrl = builder.deleteDataStream(datastreamId);
    const deleteDsResult = await httpRequest('DELETE', deleteDsUrl);
    if (deleteDsResult.status === 204) {
      console.log(pct(`DELETE Datastream ${datastreamId}`));
      console.log(`   Builder: builder.deleteDataStream('${datastreamId}') → "${deleteDsUrl}"`);
      // Remove from cleanup since we've already deleted it
      const idx = cleanup.findIndex(c => c.id === datastreamId);
      if (idx >= 0) cleanup.splice(idx, 1);

      // Verify deletion
      const verifyDs = await httpRequest('GET', builder.getDataStream(datastreamId));
      console.log(`   Verification GET: ${verifyDs.status} (expected 404)`);
      results.push({
        name: 'DELETE Datastream',
        passed: true,
        builderMethod: `builder.deleteDataStream('${datastreamId}')`,
        generatedUrl: deleteDsUrl,
        httpMethod: `DELETE ${deleteDsResult.status}`,
        httpStatus: deleteDsResult.status,
        details: `Deleted, verification GET: ${verifyDs.status}`,
      });
    } else {
      console.log(pfl(`DELETE Datastream FAILED: ${deleteDsResult.status}`));
      results.push({
        name: 'DELETE Datastream',
        passed: false,
        builderMethod: `builder.deleteDataStream('${datastreamId}')`,
        generatedUrl: deleteDsUrl,
        httpMethod: `DELETE ${deleteDsResult.status}`,
        httpStatus: deleteDsResult.status,
        details: `Failed: ${deleteDsResult.status}`,
      });
    }
  }

  // 4d: Delete system (parent)
  console.log('\n--- Test 4d: DELETE System (parent) ---\n');
  const deleteSysUrl = builder.deleteSystem(systemId);
  const deleteSysResult = await httpRequest('DELETE', deleteSysUrl);
  if (deleteSysResult.status === 204) {
    console.log(pct(`DELETE System ${systemId}`));
    console.log(`   Builder: builder.deleteSystem('${systemId}') → "${deleteSysUrl}"`);
    // Remove from cleanup
    const idx = cleanup.findIndex(c => c.id === systemId);
    if (idx >= 0) cleanup.splice(idx, 1);

    // Verify deletion
    const verifySys = await httpRequest('GET', builder.getSystem(systemId));
    console.log(`   Verification GET: ${verifySys.status} (expected 404)`);
    results.push({
      name: 'DELETE System (parent)',
      passed: true,
      builderMethod: `builder.deleteSystem('${systemId}')`,
      generatedUrl: deleteSysUrl,
      httpMethod: `DELETE ${deleteSysResult.status}`,
      httpStatus: deleteSysResult.status,
      details: `Deleted, verification GET: ${verifySys.status}`,
    });
  } else {
    console.log(pfl(`DELETE System FAILED: ${deleteSysResult.status}`));
    results.push({
      name: 'DELETE System (parent)',
      passed: false,
      builderMethod: `builder.deleteSystem('${systemId}')`,
      generatedUrl: deleteSysUrl,
      httpMethod: `DELETE ${deleteSysResult.status}`,
      httpStatus: deleteSysResult.status,
      details: `Failed: ${deleteSysResult.status}`,
    });
  }

  // ═══════════════════════════════════════════════════
  //  PHASE 5: PARSER VALIDATION ON NESTED RESPONSES
  // ═══════════════════════════════════════════════════
  console.log('\n' + hr);
  console.log('  PHASE 5: PARSER VALIDATION (using existing server data)');
  console.log(hr + '\n');

  // Test parseCollectionResponse on system's datastreams
  // Use a known system with datastreams from the server
  console.log('--- Test 5a: parseCollectionResponse on system datastreams ---\n');
  const systemsList = await httpRequest('GET', builder.getSystems({ limit: 3 }));
  const knownSystems = systemsList.body?.items || [];
  let foundSystemWithDs = false;

  for (const sys of knownSystems) {
    const dsListUrl = builder.getSystemDataStreams(sys.id);
    const dsListResult = await httpRequest('GET', dsListUrl);
    if (dsListResult.status === 200) {
      try {
        const mockResponse = new Response(JSON.stringify(dsListResult.body), {
          status: 200,
          headers: { 'Content-Type': 'application/json' },
        });
        const parsed = parseCollectionResponse(mockResponse, dsListResult.body);
        console.log(pct(`parseCollectionResponse on ${sys.id} datastreams`));
        console.log(`   URL: ${dsListUrl}`);
        console.log(`   Parsed: ${parsed.items.length} items, ${parsed.links.length} links`);
        results.push({
          name: `parseCollectionResponse — system/${sys.id}/datastreams`,
          passed: true,
          builderMethod: `parseCollectionResponse() on getSystemDataStreams('${sys.id}')`,
          generatedUrl: dsListUrl,
          httpMethod: `GET ${dsListResult.status}`,
          httpStatus: dsListResult.status,
          details: `Parsed ${parsed.items.length} items, ${parsed.links.length} links`,
        });
        if (parsed.items.length > 0) foundSystemWithDs = true;
      } catch (e: any) {
        console.log(pfl(`parseCollectionResponse FAILED for ${sys.id} datastreams: ${e.message}`));
        results.push({
          name: `parseCollectionResponse — system/${sys.id}/datastreams`,
          passed: false,
          builderMethod: `parseCollectionResponse() on getSystemDataStreams('${sys.id}')`,
          generatedUrl: dsListUrl,
          httpMethod: `GET ${dsListResult.status}`,
          httpStatus: dsListResult.status,
          details: `Parser error: ${e.message}`,
          error: e.message,
        });
      }
    }
    if (foundSystemWithDs) break;  // one test with data is enough
  }

  // 5b: Test extractCSAPIFeature on a datastream response
  console.log('\n--- Test 5b: extractCSAPIFeature on individual datastream ---\n');
  const topDsList = await httpRequest('GET', builder.getDataStreams({ limit: 1 }));
  const topDsItems = topDsList.body?.items || [];
  if (topDsItems.length > 0) {
    const dsItem = topDsItems[0];
    const dsGetUrl = builder.getDataStream(dsItem.id);
    const dsGetResult = await httpRequest('GET', dsGetUrl);
    if (dsGetResult.status === 200) {
      try {
        const resourceType = getCSAPIResourceType(dsGetResult.body);
        const feature = extractCSAPIFeature(dsGetResult.body);
        console.log(pct(`extractCSAPIFeature on datastream ${dsItem.id}`));
        console.log(`   URL: ${dsGetUrl}`);
        console.log(`   Resource type: ${resourceType || 'null'}`);
        console.log(`   Feature name: ${feature?.properties?.name || 'N/A'}`);
        results.push({
          name: `extractCSAPIFeature — datastream/${dsItem.id}`,
          passed: true,
          builderMethod: `extractCSAPIFeature(response) on getDataStream('${dsItem.id}')`,
          generatedUrl: dsGetUrl,
          httpMethod: `GET ${dsGetResult.status}`,
          httpStatus: dsGetResult.status,
          details: `Type: ${resourceType}, Name: ${feature?.properties?.name || 'N/A'}`,
        });
      } catch (e: any) {
        console.log(pfl(`extractCSAPIFeature FAILED: ${e.message}`));
        results.push({
          name: `extractCSAPIFeature — datastream/${dsItem.id}`,
          passed: false,
          builderMethod: `extractCSAPIFeature(response) on getDataStream('${dsItem.id}')`,
          generatedUrl: dsGetUrl,
          httpMethod: `GET ${dsGetResult.status}`,
          httpStatus: dsGetResult.status,
          details: `Parser error: ${e.message}`,
          error: e.message,
        });
      }
    }
  } else {
    console.log('   No datastreams available for parser test');
  }

  // ═══════════════════════════════════════════════════
  //  CLEANUP
  // ═══════════════════════════════════════════════════
  if (cleanup.length > 0) {
    console.log('\n=== Cleanup: Deleting remaining test resources ===\n');
    for (const { type, id, url } of cleanup) {
      const del = await httpRequest('DELETE', url);
      console.log(`   Delete ${type} ${id}: ${del.status}`);
    }
  }

  // ═══════════════════════════════════════════════════
  //  SUMMARY
  // ═══════════════════════════════════════════════════
  await writeResults();
}

async function writeResults() {
  const passed = results.filter(r => r.passed).length;
  const failed = results.filter(r => !r.passed).length;
  const findings = results.filter(r => r.finding);

  console.log('\n╔' + '═'.repeat(60) + '╗');
  console.log('║                     TEST SUMMARY                          ║');
  console.log('╚' + '═'.repeat(60) + '╝');
  console.log(`\nTotal: ${results.length} | Passed: ${passed} | Failed: ${failed}\n`);

  if (findings.length > 0) {
    console.log('KEY FINDINGS:');
    for (const f of findings) {
      console.log(`  ⚠ ${f.finding}`);
    }
    console.log('');
  }

  if (failed > 0) {
    console.log('FAILED TESTS:');
    for (const r of results.filter(r => !r.passed)) {
      console.log(`  ✗ ${r.name}`);
      console.log(`     ${r.builderMethod} → "${r.generatedUrl}"`);
      console.log(`     HTTP ${r.httpStatus}: ${r.details}`);
    }
    console.log('');
  }

  console.log('PASSED TESTS:');
  for (const r of results.filter(r => r.passed)) {
    console.log(`  ✓ ${r.name}`);
  }

  // Write JSON results
  const output = {
    date: new Date().toISOString(),
    testSuite: 'nested-creates',
    total: results.length,
    passed,
    failed,
    findings: findings.map(f => f.finding),
    results,
  };

  const { writeFileSync } = await import('fs');
  writeFileSync('examples/e2e-nested-results.json', JSON.stringify(output, null, 2));
  console.log('\nResults written to examples/e2e-nested-results.json');
}

main().catch(console.error);
