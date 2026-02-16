/**
 * End-to-End Write Operations Test
 *
 * This script validates that the CSAPIQueryBuilder produces correct URLs for
 * all CRUD operations by sending real HTTP requests to the live OSH SensorHub
 * server. This is the critical validation gap identified in the Library
 * Integration Report — we've confirmed GET URLs work, but POST/PUT/DELETE
 * have never been tested against a real server.
 *
 * Usage:
 *   npx tsx examples/e2e-write-operations.ts
 *
 * Prerequisites:
 *   - OSH SensorHub must be running at http://45.55.99.236:8080/sensorhub/api
 *   - Credentials: admin/admin
 */

import CSAPIQueryBuilder from '../src/ogc-api/csapi/url_builder.js';
import { scanCsapiLinks } from '../src/ogc-api/csapi/helpers.js';
import { parseCollectionResponse } from '../src/ogc-api/csapi/formats/response.js';
import { extractCSAPIFeature, getCSAPIResourceType } from '../src/ogc-api/csapi/formats/geojson.js';
import { CSAPIResourceTypes } from '../src/ogc-api/csapi/model.js';
import type { OgcApiCollectionInfo } from '../src/ogc-api/model.js';

// ========================================
// Configuration
// ========================================

const BASE_URL = 'http://45.55.99.236:8080/sensorhub/api';
const AUTH = 'Basic ' + Buffer.from('admin:admin').toString('base64');

// ========================================
// HTTP Helpers
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
}

const results: TestResult[] = [];

function logResult(r: TestResult): void {
  const icon = r.passed ? '✅' : '❌';
  console.log(`${icon} ${r.name}`);
  console.log(`   Builder: ${r.builderMethod} → "${r.generatedUrl}"`);
  console.log(`   HTTP: ${r.httpMethod} ${r.httpStatus} — ${r.details}`);
  if (r.error) console.log(`   Error: ${r.error}`);
  console.log();
  results.push(r);
}

// ========================================
// Builder Setup
// ========================================

async function setupBuilder(): Promise<CSAPIQueryBuilder> {
  console.log('=== Setting Up CSAPIQueryBuilder ===\n');

  // Fetch landing page
  const landingResult = await httpRequest('GET', '/');
  console.log(`Landing page: ${landingResult.status} ${landingResult.statusText}`);

  const landingPage = landingResult.body;
  const links = landingPage.links || [];

  // Scan for CSAPI links
  const scannedLinks = scanCsapiLinks(links);
  console.log(`scanCsapiLinks found: ${scannedLinks.size} resource types`);
  for (const [type, href] of scannedLinks) {
    console.log(`  ${type} → ${href}`);
  }

  // Build resourceUrls as relative paths (same pattern as demo bridge)
  const resourceUrls = new Map<string, string>();
  if (scannedLinks.size > 0) {
    for (const [type, href] of scannedLinks) {
      // Convert absolute href → relative path
      const url = new URL(href);
      resourceUrls.set(type, url.pathname.replace('/sensorhub/api', ''));
    }
  } else {
    // Fallback: assume all resource types at standard paths
    for (const type of CSAPIResourceTypes) {
      resourceUrls.set(type, `/${type}`);
    }
  }

  // Build synthetic collection
  const syntheticLinks = Array.from(resourceUrls).map(([type, url]) => ({
    rel: type,
    href: url,
  }));
  syntheticLinks.push({ rel: 'self', href: '/' });

  const collectionInfo = {
    id: 'e2e-test',
    title: 'E2E Write Operations Test',
    links: syntheticLinks,
  } as OgcApiCollectionInfo;

  const builder = new CSAPIQueryBuilder(collectionInfo, resourceUrls);
  console.log(`\nBuilder created. Available resources: [${[...builder.availableResources].join(', ')}]`);
  console.log();

  return builder;
}

// ========================================
// Test Functions
// ========================================

async function testCreateSystem(builder: CSAPIQueryBuilder): Promise<string | null> {
  console.log('=== Test: CREATE System ===\n');

  const url = builder.createSystem();
  const payload = {
    type: 'Feature',
    properties: {
      uid: `urn:csapi-explorer:e2e-test:system:${Date.now()}`,
      featureType: 'http://www.w3.org/ns/sosa/Sensor',
      name: 'E2E Test System — CSAPI Explorer',
      description: 'Temporary system created by e2e-write-operations.ts to validate CSAPIQueryBuilder URL generation.',
      validTime: [new Date().toISOString(), 'now'],
    },
    geometry: null,
  };

  const result = await httpRequest('POST', url, payload, 'application/geo+json');
  const locationHeader = result.headers['location'] || '';

  // Extract created ID from Location header or response body
  let createdId: string | null = null;
  if (locationHeader) {
    const parts = locationHeader.split('/');
    createdId = parts[parts.length - 1];
  } else if (result.body?.id) {
    createdId = result.body.id;
  }

  const passed = result.status === 201;

  logResult({
    name: 'CREATE System (POST to collection URL)',
    passed,
    builderMethod: 'builder.createSystem()',
    generatedUrl: url,
    httpMethod: `POST ${result.status}`,
    httpStatus: result.status,
    details: passed
      ? `Created! Location: ${locationHeader}, ID: ${createdId}`
      : `Failed: ${result.status} ${result.statusText}`,
    serverResponse: result.body,
    error: !passed ? JSON.stringify(result.body) : undefined,
  });

  return createdId;
}

async function testGetSystem(builder: CSAPIQueryBuilder, id: string): Promise<void> {
  console.log('=== Test: GET System (by ID) ===\n');

  const url = builder.getSystem(id);
  const result = await httpRequest('GET', url);
  const passed = result.status === 200;

  // Also test library parser
  let parserResult = '';
  if (passed && result.body) {
    const resourceType = getCSAPIResourceType(result.body);
    if (resourceType) {
      const feature = extractCSAPIFeature(result.body);
      parserResult = ` | Library recognized as: ${resourceType}, name="${feature.properties.name}"`;
    } else {
      parserResult = ' | Library: getCSAPIResourceType() returned null';
    }
  }

  logResult({
    name: `GET System (individual resource) ${parserResult}`,
    passed,
    builderMethod: `builder.getSystem('${id}')`,
    generatedUrl: url,
    httpMethod: `GET ${result.status}`,
    httpStatus: result.status,
    details: passed
      ? `Retrieved: ${result.body?.properties?.name || result.body?.name || 'unknown'}${parserResult}`
      : `Failed: ${result.status} ${result.statusText}`,
    serverResponse: result.body,
    error: !passed ? JSON.stringify(result.body) : undefined,
  });
}

async function testUpdateSystem(builder: CSAPIQueryBuilder, id: string): Promise<void> {
  console.log('=== Test: UPDATE System ===\n');

  const url = builder.updateSystem(id);

  // First retrieve current state
  const current = await httpRequest('GET', builder.getSystem(id));
  if (current.status !== 200) {
    logResult({
      name: 'UPDATE System (PUT existing resource)',
      passed: false,
      builderMethod: `builder.updateSystem('${id}')`,
      generatedUrl: url,
      httpMethod: 'PUT (skipped)',
      httpStatus: 0,
      details: `Could not retrieve current system: ${current.status}`,
    });
    return;
  }

  // Modify the name
  const updatedPayload = { ...current.body };
  if (updatedPayload.properties) {
    updatedPayload.properties.name = 'E2E Test System — UPDATED';
    updatedPayload.properties.description = 'Updated by e2e-write-operations.ts at ' + new Date().toISOString();
  }

  const result = await httpRequest('PUT', url, updatedPayload, 'application/geo+json');
  const passed = result.status === 200 || result.status === 204;

  logResult({
    name: 'UPDATE System (PUT existing resource)',
    passed,
    builderMethod: `builder.updateSystem('${id}')`,
    generatedUrl: url,
    httpMethod: `PUT ${result.status}`,
    httpStatus: result.status,
    details: passed
      ? `Updated successfully (${result.status})`
      : `Failed: ${result.status} ${result.statusText}`,
    serverResponse: result.body,
    error: !passed ? JSON.stringify(result.body) : undefined,
  });

  // Verify the update by re-reading
  if (passed) {
    const verify = await httpRequest('GET', builder.getSystem(id));
    const verifyName = verify.body?.properties?.name;
    console.log(`   Verification GET: name = "${verifyName}" (expected "E2E Test System — UPDATED")`);
    console.log(`   Update verified: ${verifyName === 'E2E Test System — UPDATED' ? '✅' : '⚠️ name mismatch'}`);
    console.log();
  }
}

async function testDeleteSystem(builder: CSAPIQueryBuilder, id: string): Promise<void> {
  console.log('=== Test: DELETE System ===\n');

  const url = builder.deleteSystem(id);
  const result = await httpRequest('DELETE', url);
  const passed = result.status === 200 || result.status === 204;

  logResult({
    name: 'DELETE System (DELETE individual resource)',
    passed,
    builderMethod: `builder.deleteSystem('${id}')`,
    generatedUrl: url,
    httpMethod: `DELETE ${result.status}`,
    httpStatus: result.status,
    details: passed
      ? `Deleted successfully (${result.status})`
      : `Failed: ${result.status} ${result.statusText}`,
    serverResponse: result.body,
    error: !passed ? JSON.stringify(result.body) : undefined,
  });

  // Verify the delete by trying to GET
  if (passed) {
    const verify = await httpRequest('GET', builder.getSystem(id));
    console.log(`   Verification GET after delete: ${verify.status} (expected 404)`);
    console.log(`   Delete verified: ${verify.status === 404 ? '✅' : '⚠️ unexpected status'}`);
    console.log();
  }
}

async function testCreateDeployment(builder: CSAPIQueryBuilder): Promise<string | null> {
  console.log('=== Test: CREATE Deployment ===\n');

  const url = builder.createDeployment();
  const payload = {
    type: 'Feature',
    properties: {
      uid: `urn:csapi-explorer:e2e-test:deployment:${Date.now()}`,
      featureType: 'http://www.w3.org/ns/ssn/Deployment',
      name: 'E2E Test Deployment — CSAPI Explorer',
      description: 'Temporary deployment created for library validation.',
      validTime: [new Date().toISOString(), 'now'],
    },
    geometry: null,
  };

  const result = await httpRequest('POST', url, payload, 'application/geo+json');
  const locationHeader = result.headers['location'] || '';
  let createdId: string | null = null;
  if (locationHeader) {
    createdId = locationHeader.split('/').pop() || null;
  } else if (result.body?.id) {
    createdId = result.body.id;
  }

  const passed = result.status === 201;

  logResult({
    name: 'CREATE Deployment (POST to collection URL)',
    passed,
    builderMethod: 'builder.createDeployment()',
    generatedUrl: url,
    httpMethod: `POST ${result.status}`,
    httpStatus: result.status,
    details: passed
      ? `Created! Location: ${locationHeader}, ID: ${createdId}`
      : `Failed: ${result.status} ${result.statusText}`,
    serverResponse: result.body,
    error: !passed ? JSON.stringify(result.body) : undefined,
  });

  return createdId;
}

async function testCreateProcedure(builder: CSAPIQueryBuilder): Promise<string | null> {
  console.log('=== Test: CREATE Procedure ===\n');

  const url = builder.createProcedure();
  const payload = {
    type: 'Feature',
    properties: {
      uid: `urn:csapi-explorer:e2e-test:procedure:${Date.now()}`,
      featureType: 'http://www.w3.org/ns/sosa/Procedure',
      name: 'E2E Test Procedure — CSAPI Explorer',
      description: 'Temporary procedure created for library validation.',
    },
    geometry: null,
  };

  const result = await httpRequest('POST', url, payload, 'application/geo+json');
  const locationHeader = result.headers['location'] || '';
  let createdId: string | null = null;
  if (locationHeader) {
    createdId = locationHeader.split('/').pop() || null;
  } else if (result.body?.id) {
    createdId = result.body.id;
  }

  const passed = result.status === 201;

  logResult({
    name: 'CREATE Procedure (POST to collection URL)',
    passed,
    builderMethod: 'builder.createProcedure()',
    generatedUrl: url,
    httpMethod: `POST ${result.status}`,
    httpStatus: result.status,
    details: passed
      ? `Created! Location: ${locationHeader}, ID: ${createdId}`
      : `Failed: ${result.status} ${result.statusText}`,
    serverResponse: result.body,
    error: !passed ? JSON.stringify(result.body) : undefined,
  });

  return createdId;
}

async function testCreateDatastream(builder: CSAPIQueryBuilder, systemId: string): Promise<string | null> {
  console.log('=== Test: CREATE Datastream ===\n');

  const url = builder.createDataStream();
  const payload = {
    name: 'E2E Test Datastream — CSAPI Explorer',
    description: 'Temporary datastream for library validation.',
    outputName: 'testOutput',
    system: `${BASE_URL}/systems/${systemId}`,
    observedProperties: [
      {
        definition: 'http://www.opengis.net/def/property/OGC/0/AirTemperature',
        label: 'Air Temperature',
      },
    ],
    schema: {
      obsFormat: 'application/json',
      resultSchema: {
        type: 'object',
        properties: {
          time: { type: 'string', format: 'date-time' },
          value: { type: 'number' },
        },
      },
    },
  };

  const result = await httpRequest('POST', url, payload, 'application/json');
  const locationHeader = result.headers['location'] || '';
  let createdId: string | null = null;
  if (locationHeader) {
    createdId = locationHeader.split('/').pop() || null;
  } else if (result.body?.id) {
    createdId = result.body.id;
  }

  const passed = result.status === 201;

  logResult({
    name: 'CREATE Datastream (POST to collection URL)',
    passed,
    builderMethod: 'builder.createDataStream()',
    generatedUrl: url,
    httpMethod: `POST ${result.status}`,
    httpStatus: result.status,
    details: passed
      ? `Created! Location: ${locationHeader}, ID: ${createdId}`
      : `Failed: ${result.status} ${result.statusText}`,
    serverResponse: result.body,
    error: !passed ? JSON.stringify(result.body).substring(0, 500) : undefined,
  });

  return createdId;
}

async function testCreateObservation(builder: CSAPIQueryBuilder, datastreamId: string): Promise<string | null> {
  console.log('=== Test: CREATE Observation (nested under datastream) ===\n');

  // This is the critical nested creation test:
  // createObservation(datastreamId) should produce /datastreams/{id}/observations
  const url = builder.createObservation(datastreamId);
  console.log(`   Generated URL: ${url}`);
  console.log(`   Expected pattern: /datastreams/${datastreamId}/observations`);

  const payload = {
    phenomenonTime: new Date().toISOString(),
    resultTime: new Date().toISOString(),
    result: {
      time: new Date().toISOString(),
      value: 23.5,
    },
  };

  const result = await httpRequest('POST', url, payload, 'application/json');
  const locationHeader = result.headers['location'] || '';
  let createdId: string | null = null;
  if (locationHeader) {
    createdId = locationHeader.split('/').pop() || null;
  } else if (result.body?.id) {
    createdId = result.body.id;
  }

  const passed = result.status === 201;

  logResult({
    name: 'CREATE Observation (nested POST under datastream)',
    passed,
    builderMethod: `builder.createObservation('${datastreamId}')`,
    generatedUrl: url,
    httpMethod: `POST ${result.status}`,
    httpStatus: result.status,
    details: passed
      ? `Created! Location: ${locationHeader}, ID: ${createdId}`
      : `Failed: ${result.status} ${result.statusText}`,
    serverResponse: result.body,
    error: !passed ? JSON.stringify(result.body).substring(0, 500) : undefined,
  });

  return createdId;
}

async function testListWithQueryOptions(builder: CSAPIQueryBuilder): Promise<void> {
  console.log('=== Test: LIST Systems with Query Options ===\n');

  // Test limit
  const urlLimit = builder.getSystems({ limit: 2 });
  const resultLimit = await httpRequest('GET', urlLimit);
  const parsedLimit = resultLimit.status === 200 ? parseCollectionResponse(resultLimit.body) : null;

  logResult({
    name: 'LIST Systems with limit=2',
    passed: resultLimit.status === 200 && (parsedLimit?.items?.length || 0) <= 2,
    builderMethod: "builder.getSystems({ limit: 2 })",
    generatedUrl: urlLimit,
    httpMethod: `GET ${resultLimit.status}`,
    httpStatus: resultLimit.status,
    details: `Returned ${parsedLimit?.items?.length || 0} items (requested limit=2). numberMatched=${parsedLimit?.numberMatched ?? 'N/A'}`,
  });

  // Test q (text search)
  const urlSearch = builder.getSystems({ q: 'drone' });
  const resultSearch = await httpRequest('GET', urlSearch);
  const parsedSearch = resultSearch.status === 200 ? parseCollectionResponse(resultSearch.body) : null;

  logResult({
    name: 'LIST Systems with q="drone"',
    passed: resultSearch.status === 200,
    builderMethod: "builder.getSystems({ q: 'drone' })",
    generatedUrl: urlSearch,
    httpMethod: `GET ${resultSearch.status}`,
    httpStatus: resultSearch.status,
    details: `Returned ${parsedSearch?.items?.length || 0} items matching "drone"`,
  });

  // Test limit + offset (pagination)
  const urlPage2 = builder.getSystems({ limit: 2, offset: 2 });
  const resultPage2 = await httpRequest('GET', urlPage2);
  const parsedPage2 = resultPage2.status === 200 ? parseCollectionResponse(resultPage2.body) : null;

  logResult({
    name: 'LIST Systems with limit=2, offset=2 (pagination)',
    passed: resultPage2.status === 200,
    builderMethod: "builder.getSystems({ limit: 2, offset: 2 })",
    generatedUrl: urlPage2,
    httpMethod: `GET ${resultPage2.status}`,
    httpStatus: resultPage2.status,
    details: `Returned ${parsedPage2?.items?.length || 0} items at offset=2. Links: ${parsedPage2?.links?.length || 0}`,
  });
}

async function testParseCollectionResponseOnAllTypes(builder: CSAPIQueryBuilder): Promise<void> {
  console.log('=== Test: parseCollectionResponse across resource types ===\n');

  const types: string[] = ['systems', 'deployments', 'procedures', 'datastreams', 'observations'];

  for (const type of types) {
    let url: string;
    try {
      switch (type) {
        case 'systems': url = builder.getSystems({ limit: 2 }); break;
        case 'deployments': url = builder.getDeployments({ limit: 2 }); break;
        case 'procedures': url = builder.getProcedures({ limit: 2 }); break;
        case 'datastreams': url = builder.getDataStreams({ limit: 2 }); break;
        case 'observations': url = builder.getObservations({ limit: 2 }); break;
        default: continue;
      }
    } catch {
      console.log(`   ⏭️  ${type}: Not available on builder, skipping`);
      continue;
    }

    const result = await httpRequest('GET', url);
    if (result.status !== 200) {
      logResult({
        name: `parseCollectionResponse — ${type}`,
        passed: false,
        builderMethod: `builder.get${type.charAt(0).toUpperCase() + type.slice(1)}({ limit: 2 })`,
        generatedUrl: url,
        httpMethod: `GET ${result.status}`,
        httpStatus: result.status,
        details: `GET failed: ${result.status}`,
      });
      continue;
    }

    try {
      const parsed = parseCollectionResponse(result.body);
      const itemCount = parsed.items?.length || 0;
      const hasLinks = (parsed.links?.length || 0) > 0;

      logResult({
        name: `parseCollectionResponse — ${type}`,
        passed: true,
        builderMethod: `parseCollectionResponse(response) for ${type}`,
        generatedUrl: url,
        httpMethod: `GET ${result.status}`,
        httpStatus: result.status,
        details: `Parsed ${itemCount} items, ${parsed.links?.length || 0} links, numberMatched=${parsed.numberMatched ?? 'N/A'}, numberReturned=${parsed.numberReturned ?? 'N/A'}`,
      });
    } catch (e) {
      logResult({
        name: `parseCollectionResponse — ${type}`,
        passed: false,
        builderMethod: `parseCollectionResponse(response) for ${type}`,
        generatedUrl: url,
        httpMethod: `GET ${result.status}`,
        httpStatus: result.status,
        details: `Parser threw: ${e}`,
        error: String(e),
      });
    }
  }
}

async function testCleanup(builder: CSAPIQueryBuilder, ids: { systems: string[], deployments: string[], procedures: string[], datastreams: string[] }): Promise<void> {
  console.log('=== Cleanup: Deleting test resources ===\n');

  // Delete in reverse dependency order: observations first, then datastreams, then systems

  for (const dsId of ids.datastreams) {
    try {
      const url = builder.deleteDataStream(dsId);
      const result = await httpRequest('DELETE', url);
      console.log(`   Delete datastream ${dsId}: ${result.status}`);
    } catch (e) {
      console.log(`   Delete datastream ${dsId}: FAILED — ${e}`);
    }
  }

  for (const procId of ids.procedures) {
    try {
      const url = builder.deleteProcedure(procId);
      const result = await httpRequest('DELETE', url);
      console.log(`   Delete procedure ${procId}: ${result.status}`);
    } catch (e) {
      console.log(`   Delete procedure ${procId}: FAILED — ${e}`);
    }
  }

  for (const depId of ids.deployments) {
    try {
      const url = builder.deleteDeployment(depId);
      const result = await httpRequest('DELETE', url);
      console.log(`   Delete deployment ${depId}: ${result.status}`);
    } catch (e) {
      console.log(`   Delete deployment ${depId}: FAILED — ${e}`);
    }
  }

  for (const sysId of ids.systems) {
    try {
      const url = builder.deleteSystem(sysId);
      const result = await httpRequest('DELETE', url);
      console.log(`   Delete system ${sysId}: ${result.status}`);
    } catch (e) {
      console.log(`   Delete system ${sysId}: FAILED — ${e}`);
    }
  }

  console.log();
}

// ========================================
// Main
// ========================================

async function main(): Promise<void> {
  console.log('╔════════════════════════════════════════════════════════════╗');
  console.log('║    CSAPIQueryBuilder — End-to-End Write Operations Test    ║');
  console.log('╠════════════════════════════════════════════════════════════╣');
  console.log('║ Target: OSH SensorHub at ' + BASE_URL.padEnd(33) + '║');
  console.log('║ Auth:   admin/admin                                       ║');
  console.log('║ Date:   ' + new Date().toISOString().padEnd(49) + '║');
  console.log('╚════════════════════════════════════════════════════════════╝');
  console.log();

  const builder = await setupBuilder();
  const createdIds = {
    systems: [] as string[],
    deployments: [] as string[],
    procedures: [] as string[],
    datastreams: [] as string[],
  };

  try {
    // ---- Phase 1: Read Operations (confirm baseline) ----
    console.log('━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━');
    console.log('  PHASE 1: READ OPERATIONS (Baseline Verification)');
    console.log('━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n');

    await testListWithQueryOptions(builder);
    await testParseCollectionResponseOnAllTypes(builder);

    // ---- Phase 2: Create Operations ----
    console.log('━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━');
    console.log('  PHASE 2: CREATE OPERATIONS');
    console.log('━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n');

    const systemId = await testCreateSystem(builder);
    if (systemId) createdIds.systems.push(systemId);

    const deploymentId = await testCreateDeployment(builder);
    if (deploymentId) createdIds.deployments.push(deploymentId);

    const procedureId = await testCreateProcedure(builder);
    if (procedureId) createdIds.procedures.push(procedureId);

    // Create a datastream linked to our new system
    if (systemId) {
      const datastreamId = await testCreateDatastream(builder, systemId);
      if (datastreamId) createdIds.datastreams.push(datastreamId);

      // Create an observation nested under the datastream
      if (datastreamId) {
        await testCreateObservation(builder, datastreamId);
      }
    }

    // ---- Phase 3: Read-Back Created Resources ----
    console.log('━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━');
    console.log('  PHASE 3: READ-BACK CREATED RESOURCES');
    console.log('━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n');

    if (systemId) {
      await testGetSystem(builder, systemId);
    }

    // ---- Phase 4: Update Operations ----
    console.log('━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━');
    console.log('  PHASE 4: UPDATE OPERATIONS');
    console.log('━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n');

    if (systemId) {
      await testUpdateSystem(builder, systemId);
    }

    // ---- Phase 5: Delete Operations ----
    console.log('━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━');
    console.log('  PHASE 5: DELETE OPERATIONS');
    console.log('━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n');

    if (systemId) {
      await testDeleteSystem(builder, systemId);
      // Remove from cleanup list since we already deleted it
      createdIds.systems = createdIds.systems.filter(id => id !== systemId);
    }

  } finally {
    // ---- Cleanup remaining test resources ----
    await testCleanup(builder, createdIds);
  }

  // ---- Summary ----
  console.log('╔════════════════════════════════════════════════════════════╗');
  console.log('║                     TEST SUMMARY                          ║');
  console.log('╚════════════════════════════════════════════════════════════╝');
  console.log();

  const passed = results.filter(r => r.passed).length;
  const failed = results.filter(r => !r.passed).length;
  const total = results.length;

  console.log(`Total: ${total} | Passed: ${passed} | Failed: ${failed}`);
  console.log();

  if (failed > 0) {
    console.log('FAILED TESTS:');
    for (const r of results.filter(r => !r.passed)) {
      console.log(`  ❌ ${r.name}`);
      console.log(`     ${r.builderMethod} → "${r.generatedUrl}"`);
      console.log(`     HTTP ${r.httpStatus}: ${r.details}`);
      if (r.error) console.log(`     Error: ${r.error.substring(0, 200)}`);
    }
    console.log();
  }

  console.log('PASSED TESTS:');
  for (const r of results.filter(r => r.passed)) {
    console.log(`  ✅ ${r.name}`);
  }
  console.log();

  // Write JSON results to file
  const fs = await import('fs');
  const outPath = 'examples/e2e-write-results.json';
  fs.writeFileSync(outPath, JSON.stringify({ date: new Date().toISOString(), total, passed, failed, results }, null, 2));
  console.log(`Results written to ${outPath}`);
}

main().catch((e) => {
  console.error('FATAL ERROR:', e);
  process.exit(1);
});
