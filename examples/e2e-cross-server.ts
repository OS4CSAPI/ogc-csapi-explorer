/**
 * Cross-Server Interoperability Test
 *
 * Tests CSAPIQueryBuilder and library parsers against BOTH available servers:
 *   1. OSH SensorHub — http://45.55.99.236:8080/sensorhub/api (data-rich, CRUD)
 *   2. 52North CSA   — https://csa.demo.52north.org (data via application/sml+json, read-only)
 *
 * IMPORTANT: 52North routes Accept headers to different data providers:
 *   - application/sml+json → SensorML provider → HAS DATA (3 systems, 1 deployment, 1 procedure)
 *   - application/json     → GeoJSON provider  → EMPTY (no features loaded)
 *   See: https://github.com/52North/connected-systems-pygeoapi/issues/15
 *   See: docs/implementation/f57-content-negotiation-correction.md
 *
 * This validates that the library works across different server implementations
 * with different discovery patterns, response envelopes, and naming conventions.
 *
 * Usage:
 *   npx tsx examples/e2e-cross-server.ts
 */

import CSAPIQueryBuilder from '../src/ogc-api/csapi/url_builder.js';
import { scanCsapiLinks } from '../src/ogc-api/csapi/helpers.js';
import { parseCollectionResponse } from '../src/ogc-api/csapi/formats/response.js';
import { extractCSAPIFeature, getCSAPIResourceType } from '../src/ogc-api/csapi/formats/geojson.js';
import { CSAPIResourceTypes } from '../src/ogc-api/csapi/model.js';
import type { OgcApiCollectionInfo } from '../src/ogc-api/model.js';

// ========================================
// Server Configurations
// ========================================

interface ServerConfig {
  name: string;
  baseUrl: string;
  auth?: string;
  acceptHeader?: string; // Content-type for Accept header (critical for 52North — see Issue #15)
  tlsReject?: boolean;
  discoveryMode: 'root-links' | 'collection-links' | 'both';
  hasData: boolean;
  supportsCrud: boolean;
}

const SERVERS: ServerConfig[] = [
  {
    name: 'OSH SensorHub',
    baseUrl: 'http://45.55.99.236:8080/sensorhub/api',
    auth: 'Basic ' + Buffer.from('admin:admin').toString('base64'),
    discoveryMode: 'root-links',
    hasData: true,
    supportsCrud: true,
  },
  {
    name: '52North CSA',
    baseUrl: 'https://csa.demo.52north.org',
    acceptHeader: 'application/sml+json', // SML provider has data; application/json routes to empty GeoJSON provider
    tlsReject: false,
    discoveryMode: 'collection-links',
    hasData: true, // 3 systems, 1 deployment, 1 procedure (via SML provider)
    supportsCrud: false,
  },
];

// ========================================
// HTTP Helper
// ========================================

interface HttpResult {
  status: number;
  statusText: string;
  headers: Record<string, string>;
  body: any;
  ok: boolean;
}

async function httpRequest(
  server: ServerConfig,
  method: string,
  path: string,
  body?: object,
  contentType?: string,
  acceptOverride?: string
): Promise<HttpResult> {
  const url = path.startsWith('http') ? path : `${server.baseUrl}${path}`;
  const accept = acceptOverride || server.acceptHeader || 'application/json';
  const headers: Record<string, string> = { Accept: accept };
  if (server.auth) headers['Authorization'] = server.auth;
  if (body && contentType) headers['Content-Type'] = contentType;

  try {
    const response = await fetch(url, {
      method,
      headers,
      body: body ? JSON.stringify(body) : undefined,
    });

    let responseBody: any;
    const text = await response.text();
    try { responseBody = JSON.parse(text); } catch { responseBody = text; }

    const responseHeaders: Record<string, string> = {};
    response.headers.forEach((v, k) => { responseHeaders[k] = v; });

    return { status: response.status, statusText: response.statusText, headers: responseHeaders, body: responseBody, ok: response.ok };
  } catch (e: any) {
    return { status: 0, statusText: e.message, headers: {}, body: null, ok: false };
  }
}

// ========================================
// Result Tracking
// ========================================

interface TestResult {
  server: string;
  category: string;
  name: string;
  passed: boolean;
  details: string;
  url?: string;
  httpStatus?: number;
  finding?: string;
}

const results: TestResult[] = [];
function pass(server: string, category: string, name: string, details: string, extra?: Partial<TestResult>) {
  results.push({ server, category, name, passed: true, details, ...extra });
  console.log(`  \x1b[32m✓\x1b[0m ${name}`);
  if (details) console.log(`    ${details}`);
}
function fail(server: string, category: string, name: string, details: string, extra?: Partial<TestResult>) {
  results.push({ server, category, name, passed: false, details, ...extra });
  console.log(`  \x1b[31m✗\x1b[0m ${name}`);
  if (details) console.log(`    ${details}`);
}

// ========================================
// Test Functions
// ========================================

async function testLandingPage(server: ServerConfig) {
  const category = 'Landing Page';
  console.log(`\n--- ${category} ---`);

  const r = await httpRequest(server, 'GET', '/');
  if (r.ok) {
    pass(server.name, category, 'Landing page accessible', `Status: ${r.status}`, { httpStatus: r.status });
  } else {
    fail(server.name, category, 'Landing page accessible', `Status: ${r.status} ${r.statusText}`, { httpStatus: r.status });
    return null;
  }

  // Check for title
  if (r.body?.title) {
    pass(server.name, category, 'Has title', `"${r.body.title}"`);
  } else {
    fail(server.name, category, 'Has title', 'No title in landing page');
  }

  // Check for links
  const links = r.body?.links || [];
  pass(server.name, category, 'Links array', `${links.length} links found`);

  // Check for collections link
  const dataLink = links.find((l: any) => l.rel === 'data');
  if (dataLink) {
    pass(server.name, category, 'Has "data" link (collections)', `→ ${dataLink.href}`);
  } else {
    fail(server.name, category, 'Has "data" link (collections)', 'Missing rel="data" link',
      { finding: `${server.name}: No "data" link on landing page` });
  }

  return r.body;
}

async function testConformance(server: ServerConfig) {
  const category = 'Conformance';
  console.log(`\n--- ${category} ---`);

  const r = await httpRequest(server, 'GET', '/conformance');
  if (!r.ok) {
    fail(server.name, category, 'Conformance endpoint', `Status: ${r.status}`, { httpStatus: r.status });
    return;
  }
  pass(server.name, category, 'Conformance endpoint', `Status: ${r.status}`, { httpStatus: r.status });

  const classes = r.body?.conformsTo || [];
  pass(server.name, category, 'Conformance classes count', `${classes.length} classes`);

  // Check for CSA-specific classes
  const csaClasses = classes.filter((c: string) => c.includes('23-001') || c.includes('23-002') || c.includes('connected'));
  if (csaClasses.length > 0) {
    pass(server.name, category, 'CSA conformance classes', `${csaClasses.length} CSA classes found`);
  } else {
    fail(server.name, category, 'CSA conformance classes', 'No CSA conformance classes declared',
      { finding: `${server.name}: Server does not advertise CSA conformance classes` });
  }
}

async function testContentNegotiation(server: ServerConfig) {
  const category = 'Content Negotiation';
  console.log(`\n--- ${category} ---`);

  // Test both Accept headers to document the routing behavior
  // This is the core Issue #15 validation — see https://github.com/52North/connected-systems-pygeoapi/issues/15
  const acceptHeaders = [
    { accept: 'application/json', label: 'application/json' },
    { accept: 'application/sml+json', label: 'application/sml+json' },
    { accept: 'application/geo+json', label: 'application/geo+json' },
  ];

  for (const { accept, label } of acceptHeaders) {
    const r = await httpRequest(server, 'GET', '/systems?limit=5', undefined, undefined, accept);
    if (r.ok) {
      const items = r.body?.features || r.body?.items || [];
      const envelope = r.body?.features ? 'features' : r.body?.items ? 'items' : 'unknown';
      const responseContentType = r.headers['content-type'] || 'none';
      pass(server.name, category, `Accept: ${label}`,
        `${items.length} items, envelope: ${envelope}, response CT: ${responseContentType}`,
        { httpStatus: r.status });

      if (items.length === 0 && server.hasData) {
        results[results.length - 1].finding =
          `${server.name}: Accept=${label} returns 0 items even though server has data (content negotiation routing — Issue #15)`;
      }
    } else {
      fail(server.name, category, `Accept: ${label}`,
        `HTTP ${r.status}`, { httpStatus: r.status });
    }
  }

  // Test with no Accept header (server default)
  const noAcceptUrl = `${server.baseUrl}/systems?limit=5`;
  try {
    const response = await fetch(noAcceptUrl, {
      headers: server.auth ? { Authorization: server.auth } : {},
    });
    const text = await response.text();
    let body: any;
    try { body = JSON.parse(text); } catch { body = text; }
    const items = body?.features || body?.items || [];
    const ct = response.headers.get('content-type') || 'none';
    pass(server.name, category, 'No Accept header (server default)',
      `${items.length} items, response CT: ${ct}`, { httpStatus: response.status });
  } catch (e: any) {
    fail(server.name, category, 'No Accept header (server default)', `Error: ${e.message}`);
  }
}

async function testDiscovery(server: ServerConfig, landingPage: any) {
  const category = 'Discovery';
  console.log(`\n--- ${category} ---`);

  // Test scanCsapiLinks on landing page
  const links = landingPage?.links || [];
  const rootLinks = scanCsapiLinks(links);
  console.log(`  scanCsapiLinks(landingPage.links): ${rootLinks.size} resource types`);
  for (const [type, href] of rootLinks) {
    console.log(`    ${type} → ${href}`);
  }
  if (rootLinks.size > 0) {
    pass(server.name, category, 'Root-level CSAPI links (scanCsapiLinks)', `Found ${rootLinks.size}: ${[...rootLinks.keys()].join(', ')}`);
  } else {
    fail(server.name, category, 'Root-level CSAPI links (scanCsapiLinks)', 'No CSAPI links found on landing page',
      { finding: `${server.name}: scanCsapiLinks finds 0 resources from landing page. Server uses collection-scoped discovery.` });
  }

  // Test collection-based discovery
  const collectionsR = await httpRequest(server, 'GET', '/collections');
  if (collectionsR.ok) {
    const collections = collectionsR.body?.collections || [];
    pass(server.name, category, 'Collections endpoint', `${collections.length} collections found`);

    // For each collection, scan its links for CSAPI resources
    let collectionResources = new Map<string, string>();
    for (const col of collections) {
      const colLinks = col.links || [];
      const colCsapi = scanCsapiLinks(colLinks);
      for (const [type, href] of colCsapi) {
        collectionResources.set(type, href);
      }
    }

    if (collectionResources.size > 0) {
      pass(server.name, category, 'Collection-scoped CSAPI links', `Found ${collectionResources.size}: ${[...collectionResources.keys()].join(', ')}`);
      for (const [type, href] of collectionResources) {
        console.log(`    ${type} → ${href}`);
      }
    } else {
      fail(server.name, category, 'Collection-scoped CSAPI links', 'No CSAPI links found in collection link relations');
    }
  } else {
    fail(server.name, category, 'Collections endpoint', `Status: ${collectionsR.status}`);
  }

  return rootLinks;
}

async function testBuilderSetup(server: ServerConfig, rootLinks: Map<string, string>) {
  const category = 'Builder Setup';
  console.log(`\n--- ${category} ---`);

  // Build resourceUrls map
  const resourceUrls = new Map<string, string>();
  if (rootLinks.size > 0) {
    for (const [type, href] of rootLinks) {
      try {
        const url = new URL(href);
        resourceUrls.set(type, url.pathname.replace(/^.*\/api/, ''));
      } catch {
        // Relative URL - use as-is
        resourceUrls.set(type, href);
      }
    }
  } else {
    // Fallback for servers without root links (52North pattern)
    for (const type of CSAPIResourceTypes) {
      resourceUrls.set(type, `/${type}`);
    }
    pass(server.name, category, 'Fallback resource URLs', `Using standard paths for ${resourceUrls.size} resource types`);
  }

  // Build synthetic collection
  const syntheticLinks = Array.from(resourceUrls).map(([type, url]) => ({
    rel: type,
    href: url,
  }));
  syntheticLinks.push({ rel: 'self', href: '/' });

  const collection = {
    id: `${server.name.toLowerCase().replace(/\s+/g, '-')}-test`,
    title: server.name,
    links: syntheticLinks,
  } as OgcApiCollectionInfo;

  try {
    const builder = new CSAPIQueryBuilder(collection, resourceUrls);
    const available = [...builder.availableResources];
    pass(server.name, category, 'CSAPIQueryBuilder created', `Available: [${available.join(', ')}]`);
    return builder;
  } catch (e: any) {
    fail(server.name, category, 'CSAPIQueryBuilder created', `Error: ${e.message}`);
    return null;
  }
}

async function testReadOperations(server: ServerConfig, builder: CSAPIQueryBuilder) {
  const category = 'Read Operations';
  console.log(`\n--- ${category} ---`);

  // Test listing each resource type
  const resourceTypes = ['systems', 'deployments', 'procedures', 'datastreams', 'observations'] as const;

  for (const type of resourceTypes) {
    let getMethod: string;
    let url: string;
    try {
      switch (type) {
        case 'systems': url = builder.getSystems({ limit: 3 }); getMethod = `getSystems({ limit: 3 })`; break;
        case 'deployments': url = builder.getDeployments({ limit: 3 }); getMethod = `getDeployments({ limit: 3 })`; break;
        case 'procedures': url = builder.getProcedures({ limit: 3 }); getMethod = `getProcedures({ limit: 3 })`; break;
        case 'datastreams': url = builder.getDatastreams({ limit: 3 }); getMethod = `getDatastreams({ limit: 3 })`; break;
        case 'observations': url = builder.getObservations({ limit: 3 }); getMethod = `getObservations({ limit: 3 })`; break;
      }
    } catch (e: any) {
      fail(server.name, category, `LIST ${type}`, `Builder error: ${e.message}`);
      continue;
    }

    const r = await httpRequest(server, 'GET', url!);
    if (r.ok) {
      const items = r.body?.features || r.body?.items || [];
      const envelope = r.body?.features ? 'FeatureCollection/features' : r.body?.items ? 'items' : 'unknown';
      pass(server.name, category, `LIST ${type}`, `${items.length} items, envelope: ${envelope}`, { url: url!, httpStatus: r.status });
    } else {
      fail(server.name, category, `LIST ${type}`, `HTTP ${r.status}: ${typeof r.body === 'object' ? JSON.stringify(r.body) : r.body}`,
        { url: url!, httpStatus: r.status, finding: `${server.name}: ${type} endpoint returned ${r.status}` });
    }
  }

  // Test query parameters
  console.log(`\n  --- Query Parameters ---`);
  for (const params of [
    { limit: 2 },
    { limit: 2, offset: 1 },
  ]) {
    const url = builder.getSystems(params);
    const paramStr = JSON.stringify(params);
    const r = await httpRequest(server, 'GET', url);
    if (r.ok) {
      const items = r.body?.features || r.body?.items || [];
      pass(server.name, category, `getSystems(${paramStr})`, `${items.length} items`, { url, httpStatus: r.status });
    } else {
      fail(server.name, category, `getSystems(${paramStr})`, `HTTP ${r.status}`, { url, httpStatus: r.status });
    }
  }
}

async function testParsers(server: ServerConfig, builder: CSAPIQueryBuilder) {
  const category = 'Parsers';
  console.log(`\n--- ${category} ---`);

  // Test parseCollectionResponse on each resource type
  const resourceTypes = ['systems', 'deployments', 'procedures', 'datastreams', 'observations'] as const;

  for (const type of resourceTypes) {
    let url: string;
    try {
      switch (type) {
        case 'systems': url = builder.getSystems({ limit: 3 }); break;
        case 'deployments': url = builder.getDeployments({ limit: 3 }); break;
        case 'procedures': url = builder.getProcedures({ limit: 3 }); break;
        case 'datastreams': url = builder.getDatastreams({ limit: 3 }); break;
        case 'observations': url = builder.getObservations({ limit: 3 }); break;
      }
    } catch {
      continue;
    }

    const r = await httpRequest(server, 'GET', url!);
    if (!r.ok) continue;

    try {
      const parsed = parseCollectionResponse(r.body);
      pass(server.name, category, `parseCollectionResponse — ${type}`,
        `${parsed.items.length} items, ${parsed.links.length} links, numberMatched=${parsed.numberMatched ?? 'N/A'}`,
        { url: url!, httpStatus: r.status });
    } catch (e: any) {
      fail(server.name, category, `parseCollectionResponse — ${type}`,
        `Error: ${e.message}`, { url: url!, httpStatus: r.status, finding: `${server.name}: parseCollectionResponse fails on ${type}: ${e.message}` });
    }
  }

  // Test extractCSAPIFeature on individual resources (only if data present)
  if (server.hasData) {
    console.log(`\n  --- Feature Extraction ---`);
    const sysUrl = builder.getSystems({ limit: 1 });
    const sysR = await httpRequest(server, 'GET', sysUrl);
    if (sysR.ok) {
      const items = sysR.body?.features || sysR.body?.items || [];
      if (items.length > 0) {
        const sysId = items[0].id;
        const detailUrl = builder.getSystem(sysId);
        const detailR = await httpRequest(server, 'GET', detailUrl);
        if (detailR.ok) {
          try {
            const resourceType = getCSAPIResourceType(detailR.body);
            const feature = extractCSAPIFeature(detailR.body);
            pass(server.name, category, `extractCSAPIFeature — system/${sysId}`,
              `type=${resourceType}, name="${feature?.properties?.name}"`,
              { url: detailUrl, httpStatus: detailR.status });
          } catch (e: any) {
            fail(server.name, category, `extractCSAPIFeature — system/${sysId}`,
              `Error: ${e.message}`, { url: detailUrl, httpStatus: detailR.status });
          }
        }
      }
    }
  }
}

async function testResponseEnvelope(server: ServerConfig, builder: CSAPIQueryBuilder) {
  const category = 'Response Envelope';
  console.log(`\n--- ${category} ---`);

  // Check which envelope format the server uses
  const url = builder.getSystems({ limit: 1 });
  const r = await httpRequest(server, 'GET', url);
  if (!r.ok) {
    fail(server.name, category, 'Envelope detection', `HTTP ${r.status}`);
    return;
  }

  const body = r.body;
  const hasFeatures = Array.isArray(body?.features);
  const hasItems = Array.isArray(body?.items);
  const hasType = body?.type === 'FeatureCollection';

  if (hasType && hasFeatures) {
    pass(server.name, category, 'Envelope format', 'Standard FeatureCollection/features (spec-compliant)');
  } else if (hasItems) {
    pass(server.name, category, 'Envelope format', 'Items envelope ({ items: [...] }) — non-standard but supported',
      { finding: `${server.name}: Uses non-standard "items" envelope instead of FeatureCollection` });
  } else {
    fail(server.name, category, 'Envelope format', `Unexpected: features=${hasFeatures}, items=${hasItems}, type=${body?.type}`);
  }

  // Check for standard response properties
  const hasLinks = Array.isArray(body?.links);
  const hasNumberMatched = typeof body?.numberMatched === 'number';
  const hasNumberReturned = typeof body?.numberReturned === 'number';
  const hasTimeStamp = typeof body?.timeStamp === 'string';

  pass(server.name, category, 'Response metadata',
    `links=${hasLinks}, numberMatched=${hasNumberMatched}, numberReturned=${hasNumberReturned}, timeStamp=${hasTimeStamp}`);
}

async function testNestedResources(server: ServerConfig, builder: CSAPIQueryBuilder) {
  const category = 'Nested Resources';
  console.log(`\n--- ${category} ---`);

  if (!server.hasData) {
    console.log('  (Skipped — no data on this server)');
    results.push({ server: server.name, category, name: 'Nested resource tests', passed: true, details: 'Skipped — no data' });
    return;
  }

  // Get a system with datastreams
  const sysUrl = builder.getSystems({ limit: 3 });
  const sysR = await httpRequest(server, 'GET', sysUrl);
  if (!sysR.ok) return;

  const systems = sysR.body?.features || sysR.body?.items || [];
  for (const sys of systems) {
    // Test getSystemDatastreams
    try {
      const dsUrl = builder.getSystemDatastreams(sys.id);
      const dsR = await httpRequest(server, 'GET', dsUrl);
      if (dsR.ok) {
        const items = dsR.body?.features || dsR.body?.items || [];
        if (items.length > 0) {
          pass(server.name, category, `getSystemDatastreams('${sys.id}')`,
            `${items.length} datastreams, envelope: ${dsR.body?.features ? 'features' : 'items'}`,
            { url: dsUrl, httpStatus: dsR.status });

          // Test parseCollectionResponse on nested response
          try {
            const parsed = parseCollectionResponse(dsR.body);
            pass(server.name, category, `parseCollectionResponse — nested datastreams`,
              `${parsed.items.length} items parsed from ${sys.id}/datastreams`,
              { url: dsUrl });
          } catch (e: any) {
            fail(server.name, category, `parseCollectionResponse — nested datastreams`,
              `Error: ${e.message}`, { url: dsUrl, finding: `${server.name}: Parser fails on nested datastream response: ${e.message}` });
          }

          // Test observation listing under a datastream
          const dsId = items[0].id;
          try {
            const obsUrl = builder.getObservationsForDatastream(dsId, { limit: 2 });
            const obsR = await httpRequest(server, 'GET', obsUrl);
            if (obsR.ok) {
              const obsItems = obsR.body?.features || obsR.body?.items || [];
              pass(server.name, category, `getObservationsForDatastream('${dsId}')`,
                `${obsItems.length} observations`, { url: obsUrl, httpStatus: obsR.status });
            } else {
              fail(server.name, category, `getObservationsForDatastream('${dsId}')`,
                `HTTP ${obsR.status}`, { url: obsUrl, httpStatus: obsR.status });
            }
          } catch (e: any) {
            fail(server.name, category, `getObservationsForDatastream`, `Builder error: ${e.message}`);
          }

          break; // One system with data is enough
        }
      }
    } catch (e: any) {
      fail(server.name, category, `getSystemDatastreams('${sys.id}')`, `Error: ${e.message}`);
    }
  }
}

async function testCrudOperations(server: ServerConfig, builder: CSAPIQueryBuilder) {
  const category = 'CRUD Operations';
  console.log(`\n--- ${category} ---`);

  if (!server.supportsCrud) {
    console.log('  (Server is read-only — testing POST to verify read-only enforcement)');

    // Attempt a create to see if server properly rejects it
    const createUrl = builder.createSystem();
    const payload = {
      type: 'Feature',
      properties: {
        uid: `urn:csapi-explorer:cross-server-test:${Date.now()}`,
        featureType: 'http://www.w3.org/ns/sosa/Platform',
        name: 'Cross-Server Test — should be rejected',
      },
    };
    const r = await httpRequest(server, 'POST', createUrl, payload, 'application/geo+json');
    if (r.status === 405 || r.status === 403 || r.status === 401) {
      pass(server.name, category, 'Read-only enforcement', `POST correctly rejected with ${r.status}`,
        { url: createUrl, httpStatus: r.status });
    } else if (r.status === 201) {
      pass(server.name, category, 'CREATE System (unexpected)', `Server accepted POST! Status: 201`,
        { url: createUrl, httpStatus: r.status, finding: `${server.name}: Server accepted write — not read-only as expected` });
    } else {
      fail(server.name, category, 'Write behavior', `Unexpected status ${r.status}: ${JSON.stringify(r.body)}`,
        { url: createUrl, httpStatus: r.status });
    }
    return;
  }

  // Full CRUD cycle on writable server
  const NOW = new Date().toISOString();
  const UNIQUE = Date.now();

  // CREATE
  const createUrl = builder.createSystem();
  const createPayload = {
    type: 'Feature',
    properties: {
      uid: `urn:csapi-explorer:cross-server:system:${UNIQUE}`,
      featureType: 'http://www.w3.org/ns/sosa/Platform',
      name: `Cross-Server Test System — ${server.name}`,
      description: 'Created by e2e-cross-server.ts',
      validTime: [NOW, 'now'],
    },
  };

  const createR = await httpRequest(server, 'POST', createUrl, createPayload, 'application/geo+json');
  const loc = createR.headers['location'] || '';
  const id = loc.split('/').pop() || '';

  if (createR.status === 201 && id) {
    pass(server.name, category, 'CREATE System', `201 Created, ID: ${id}`, { url: createUrl, httpStatus: 201 });
  } else {
    fail(server.name, category, 'CREATE System', `HTTP ${createR.status}: ${JSON.stringify(createR.body)}`,
      { url: createUrl, httpStatus: createR.status });
    return;
  }

  // READ
  const getUrl = builder.getSystem(id);
  const getR = await httpRequest(server, 'GET', getUrl);
  if (getR.ok) {
    const name = getR.body?.properties?.name || getR.body?.name;
    pass(server.name, category, 'GET System (read-back)', `name="${name}"`, { url: getUrl, httpStatus: getR.status });
  } else {
    fail(server.name, category, 'GET System (read-back)', `HTTP ${getR.status}`, { url: getUrl, httpStatus: getR.status });
  }

  // UPDATE
  const updateUrl = builder.updateSystem(id);
  const updatePayload = { ...createPayload, properties: { ...createPayload.properties, name: `Cross-Server Test — UPDATED — ${server.name}` } };
  const updateR = await httpRequest(server, 'PUT', updateUrl, updatePayload, 'application/geo+json');
  if (updateR.status === 204 || updateR.status === 200) {
    pass(server.name, category, 'UPDATE System (PUT)', `Status: ${updateR.status}`, { url: updateUrl, httpStatus: updateR.status });

    // Verify update
    const verifyR = await httpRequest(server, 'GET', getUrl);
    const verifyName = verifyR.body?.properties?.name || verifyR.body?.name;
    if (verifyName?.includes('UPDATED')) {
      pass(server.name, category, 'UPDATE verification', `name="${verifyName}"`);
    } else {
      fail(server.name, category, 'UPDATE verification', `name="${verifyName}" — expected "UPDATED" in name`);
    }
  } else {
    fail(server.name, category, 'UPDATE System (PUT)', `HTTP ${updateR.status}: ${JSON.stringify(updateR.body)}`,
      { url: updateUrl, httpStatus: updateR.status });
  }

  // DELETE
  const deleteUrl = builder.deleteSystem(id);
  const deleteR = await httpRequest(server, 'DELETE', deleteUrl);
  if (deleteR.status === 204 || deleteR.status === 200) {
    pass(server.name, category, 'DELETE System', `Status: ${deleteR.status}`, { url: deleteUrl, httpStatus: deleteR.status });

    // Verify deletion
    const verifyDelR = await httpRequest(server, 'GET', getUrl);
    if (verifyDelR.status === 404) {
      pass(server.name, category, 'DELETE verification', 'GET returns 404');
    } else {
      fail(server.name, category, 'DELETE verification', `GET returns ${verifyDelR.status} (expected 404)`);
    }
  } else {
    fail(server.name, category, 'DELETE System', `HTTP ${deleteR.status}`, { url: deleteUrl, httpStatus: deleteR.status });
    // Cleanup
    await httpRequest(server, 'DELETE', deleteUrl);
  }
}

// ========================================
// Cross-Server Comparison
// ========================================

function generateComparison() {
  console.log('\n' + '═'.repeat(70));
  console.log('  CROSS-SERVER COMPARISON');
  console.log('═'.repeat(70));

  const serverNames = SERVERS.map(s => s.name);
  const categories = [...new Set(results.map(r => r.category))];

  for (const cat of categories) {
    console.log(`\n  ${cat}:`);
    const catResults = results.filter(r => r.category === cat);
    const testNames = [...new Set(catResults.map(r => r.name))];

    for (const test of testNames) {
      const row = serverNames.map(s => {
        const r = catResults.find(r => r.server === s && r.name === test);
        if (!r) return '—';
        return r.passed ? '✓' : '✗';
      });
      const line = row.map((r, i) => `${serverNames[i]}: ${r}`).join('  |  ');
      console.log(`    ${test}: ${line}`);
    }
  }
}

// ========================================
// Main
// ========================================

async function main() {
  const hr = '═'.repeat(70);

  console.log('╔' + hr + '╗');
  console.log('║' + '    CSAPIQueryBuilder — Cross-Server Interoperability Test'.padEnd(70) + '║');
  console.log('╠' + hr + '╣');
  for (const s of SERVERS) {
    console.log('║' + `  ${s.name}: ${s.baseUrl}`.padEnd(70) + '║');
  }
  console.log('║' + `  Date: ${new Date().toISOString()}`.padEnd(70) + '║');
  console.log('╚' + hr + '╝');

  for (const server of SERVERS) {
    console.log('\n' + '▓'.repeat(70));
    console.log(`  SERVER: ${server.name}`);
    console.log(`  URL:    ${server.baseUrl}`);
    console.log(`  Mode:   ${server.discoveryMode} | Data: ${server.hasData} | CRUD: ${server.supportsCrud}`);
    console.log('▓'.repeat(70));

    // Phase 1: Landing page
    const landingPage = await testLandingPage(server);
    if (!landingPage) continue;

    // Phase 2: Conformance
    await testConformance(server);

    // Phase 3: Content negotiation (critical for 52North — Issue #15)
    await testContentNegotiation(server);

    // Phase 4: Discovery
    const rootLinks = await testDiscovery(server, landingPage);

    // Phase 5: Builder setup
    const builder = await testBuilderSetup(server, rootLinks || new Map());
    if (!builder) continue;

    // Phase 6: Read operations
    await testReadOperations(server, builder);

    // Phase 7: Response envelope analysis
    await testResponseEnvelope(server, builder);

    // Phase 8: Parser validation
    await testParsers(server, builder);

    // Phase 9: Nested resources
    await testNestedResources(server, builder);

    // Phase 10: CRUD operations
    await testCrudOperations(server, builder);
  }

  // Cross-server comparison
  generateComparison();

  // Summary
  console.log('\n' + '═'.repeat(70));
  console.log('  SUMMARY');
  console.log('═'.repeat(70));

  for (const server of SERVERS) {
    const serverResults = results.filter(r => r.server === server.name);
    const passed = serverResults.filter(r => r.passed).length;
    const failed = serverResults.filter(r => !r.passed).length;
    console.log(`\n  ${server.name}: ${passed} passed, ${failed} failed (${serverResults.length} total)`);

    if (failed > 0) {
      console.log('  Failed:');
      for (const r of serverResults.filter(r => !r.passed)) {
        console.log(`    ✗ [${r.category}] ${r.name}: ${r.details}`);
      }
    }
  }

  const findings = results.filter(r => r.finding);
  if (findings.length > 0) {
    console.log('\n  KEY FINDINGS:');
    for (const f of findings) {
      console.log(`    ⚠ ${f.finding}`);
    }
  }

  // Write JSON results
  const output = {
    date: new Date().toISOString(),
    testSuite: 'cross-server-interoperability',
    servers: SERVERS.map(s => ({ name: s.name, baseUrl: s.baseUrl, hasData: s.hasData, supportsCrud: s.supportsCrud })),
    summary: SERVERS.map(s => {
      const sr = results.filter(r => r.server === s.name);
      return { server: s.name, total: sr.length, passed: sr.filter(r => r.passed).length, failed: sr.filter(r => !r.passed).length };
    }),
    findings: findings.map(f => f.finding),
    results,
  };

  const { writeFileSync } = await import('fs');
  writeFileSync('examples/e2e-cross-server-results.json', JSON.stringify(output, null, 2));
  console.log('\n  Results written to examples/e2e-cross-server-results.json');
}

main().catch(console.error);
