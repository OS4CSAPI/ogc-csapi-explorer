/**
 * Bridge module between the CSAPI Explorer demo app and the ogc-client library.
 *
 * Integrates CSAPIQueryBuilder for URL construction and provides re-exports
 * of the library's response parsers. Components import from this module
 * instead of constructing URLs manually — this is the demo's primary
 * validation that the library's CRUD URL building works end-to-end.
 *
 * The builder produces relative paths (e.g., `/systems?limit=10`) that
 * apiFetch() prepends with the proxy base URL (e.g., `/api/52north`).
 */
import { shallowRef } from 'vue'
import CSAPIQueryBuilder from '@csapi/ogc-api/csapi/url_builder'
import { parseCollectionResponse } from '@csapi/ogc-api/csapi/formats/response'
import { extractCSAPIFeature, getCSAPIResourceType } from '@csapi/ogc-api/csapi/formats/geojson'
import { classifyFeature, inferResourceTypeFromPath } from '@csapi/ogc-api/csapi/formats/classification'
import { getContentTypeForResource } from '@csapi/ogc-api/csapi/formats/constants'
import { parseDatastream, parseObservation, parseControlStream, parseCommand, parseCommandStatus } from '@csapi/ogc-api/csapi/formats/part2'
import { parseProperty } from '@csapi/ogc-api/csapi/formats/property'
import { parseDatastreamSchemaResponse } from '@csapi/ogc-api/csapi/formats/schema-response'
import { parseSensorML30 } from '@csapi/ogc-api/csapi/formats/sensorml/parser'
import { scanCsapiLinks } from '@csapi/ogc-api/csapi/helpers'
import { CSAPIResourceTypes } from '@csapi/ogc-api/csapi/model'
import type { OgcApiCollectionInfo } from '@csapi/ogc-api/model'
import type {
  QueryOptions,
  SystemQueryOptions,
  DeploymentQueryOptions,
  DatastreamQueryOptions,
  ObservationQueryOptions,
  ControlStreamQueryOptions,
  CommandQueryOptions,
  PropertyQueryOptions,
} from '@csapi/ogc-api/csapi/model'
import type { CollectionResponse } from '@csapi/ogc-api/csapi/formats/response'

// ========================================
// URL Path Normalization
// ========================================

/**
 * Maps internal resource type keys to their OGC API URL path segments.
 *
 * Most resource types already match their URL path (e.g., 'systems' → '/systems'),
 * but 'controlStreams' is camelCase internally while the OGC Connected Systems API
 * spec uses the all-lowercase path '/controlstreams'.
 *
 * OSH enforces this: GET /controlStreams/id → 400 "Invalid resource name".
 */
const URL_PATH_OVERRIDES: Record<string, string> = {
  controlStreams: 'controlstreams',
}

/** Convert a resource type key to its URL path segment. */
function toUrlPath(resourceType: string): string {
  return URL_PATH_OVERRIDES[resourceType] ?? resourceType
}

// ========================================
// Builder Instance
// ========================================

/** The active CSAPIQueryBuilder instance. Null when not connected. */
export const builder = shallowRef<CSAPIQueryBuilder | null>(null)

/**
 * Initialize a CSAPIQueryBuilder from the connected server's discovered links.
 *
 * Discovery strategy:
 * 1. Scan landing page links for CSAPI resource links (ogc-cs: prefix,
 *    plain resource name, or items link conventions)
 * 2. Also scan collection links for additional resources
 * 3. If any CSAPI links found, use only those types (respects what the server advertises)
 * 4. Fallback: assume all 9 standard resource types are available
 *
 * Resource URLs in the builder use relative paths (e.g., `/systems`)
 * so that apiFetch() can prepend the proxy base URL transparently.
 */
export function initializeBuilder(
  landingPage: any,
  collections: any[]
): CSAPIQueryBuilder {
  // Gather all links from landing page and collections
  const allLinks: Array<{ rel?: string; href?: string }> = []

  if (Array.isArray(landingPage?.links)) {
    allLinks.push(...landingPage.links)
  }
  for (const coll of collections) {
    if (Array.isArray(coll?.links)) {
      allLinks.push(...coll.links)
    }
  }

  // Discover CSAPI resources using the library's own link scanner
  const discovered = scanCsapiLinks(allLinks)

  // Build relative resource URL map — the builder will use these paths
  // (not the absolute server URLs) so paths stay proxy-compatible
  const resourceUrls = new Map<string, string>()

  if (discovered.size > 0) {
    // Server advertises CSAPI links — use discovered types with standard path
    // toUrlPath() normalizes keys like 'controlStreams' → 'controlstreams'
    for (const type of discovered.keys()) {
      resourceUrls.set(type, `/${toUrlPath(type)}`)
    }
  } else {
    // Fallback: assume all 9 standard types at their standard paths
    for (const type of CSAPIResourceTypes) {
      resourceUrls.set(type, `/${toUrlPath(type)}`)
    }
  }

  // Build synthetic collection with links that scanCsapiLinks will recognize
  // Convention 2: plain resource name as rel → automatically populates availableResources
  const syntheticLinks = Array.from(resourceUrls).map(([type, url]) => ({
    rel: type,
    href: url,
  }))
  syntheticLinks.push({ rel: 'self', href: '/' })

  // Create the builder with a minimal collection info object
  // (only id, title, links are used by CSAPIQueryBuilder)
  const collectionInfo = {
    id: 'csapi-explorer',
    title: landingPage?.title || 'CSAPI Server',
    links: syntheticLinks,
  } as OgcApiCollectionInfo

  const newBuilder = new CSAPIQueryBuilder(collectionInfo, resourceUrls)
  builder.value = newBuilder
  return newBuilder
}

/** Clear the builder on disconnect. */
export function destroyBuilder(): void {
  builder.value = null
}

/**
 * Returns the set of resource types the builder considers available.
 * Useful for UI to show which types are supported by the connected server.
 */
export function getAvailableResources(): Set<string> {
  return builder.value?.availableResources ?? new Set()
}

// ========================================
// Generic CRUD URL Helpers
// ========================================

/**
 * Build the list URL for a resource type with query options.
 * Dispatches to the builder's type-specific method (getSystems, getDeployments, etc.)
 * which validates the resource is available and formats query parameters correctly.
 */
export function getListUrl(resourceType: string, options?: QueryOptions): string {
  const b = builder.value
  if (!b) return `/${toUrlPath(resourceType)}`

  try {
    switch (resourceType) {
      case 'systems': return b.getSystems(options as SystemQueryOptions)
      case 'deployments': return b.getDeployments(options as DeploymentQueryOptions)
      case 'procedures': return b.getProcedures(options)
      case 'samplingFeatures': return b.getSamplingFeatures(options)
      case 'properties': return b.getProperties(options as PropertyQueryOptions)
      case 'datastreams': return b.getDataStreams(options as DatastreamQueryOptions)
      case 'observations': return b.getObservations(options as ObservationQueryOptions)
      case 'controlStreams': return b.getControlStreams(options as ControlStreamQueryOptions)
      case 'commands': return b.getCommands(options as CommandQueryOptions)
      default: return `/${toUrlPath(resourceType)}`
    }
  } catch {
    // EndpointError if resource type not available — fall back to manual path
    return `/${toUrlPath(resourceType)}`
  }
}

/**
 * Build the URL for a single resource by type and ID.
 * Dispatches to getSystem(), getDeployment(), etc.
 */
export function getDetailUrl(resourceType: string, id: string): string {
  const b = builder.value
  if (!b) return `/${toUrlPath(resourceType)}/${id}`

  try {
    switch (resourceType) {
      case 'systems': return b.getSystem(id)
      case 'deployments': return b.getDeployment(id)
      case 'procedures': return b.getProcedure(id)
      case 'samplingFeatures': return b.getSamplingFeature(id)
      case 'properties': return b.getProperty(id)
      case 'datastreams': return b.getDataStream(id)
      case 'observations': return b.getObservation(id)
      case 'controlStreams': return b.getControlStream(id)
      case 'commands': return b.getCommand(id)
      default: return `/${toUrlPath(resourceType)}/${id}`
    }
  } catch {
    return `/${toUrlPath(resourceType)}/${id}`
  }
}

/**
 * Build the POST URL for creating a resource.
 * Handles nested creation: observations POST to /datastreams/{id}/observations,
 * commands POST to /controlStreams/{id}/commands.
 */
export function getCreateUrl(resourceType: string, parentId?: string): string {
  const b = builder.value
  if (!b) {
    if (resourceType === 'datastreams' && parentId) return `/systems/${parentId}/datastreams`
    if (resourceType === 'controlStreams' && parentId) return `/systems/${parentId}/controlstreams`
    if (resourceType === 'observations' && parentId) return `/datastreams/${parentId}/observations`
    if (resourceType === 'commands' && parentId) return `/controlstreams/${parentId}/commands`
    return `/${toUrlPath(resourceType)}`
  }

  try {
    switch (resourceType) {
      case 'systems': return b.createSystem()
      case 'deployments': return b.createDeployment()
      case 'procedures': return b.createProcedure()
      case 'samplingFeatures': return b.createSamplingFeature()
      // Part 2: use nested URLs via parent ID — library methods don't accept parentId
      case 'datastreams':
        return parentId ? b.getSystemDataStreams(parentId).split('?')[0] : b.createDataStream()
      case 'observations': return b.createObservation(parentId || '')
      case 'controlStreams':
        return parentId ? b.getSystemControlStreams(parentId).split('?')[0] : b.createControlStream()
      case 'commands': return b.createCommand(parentId || '')
      // Nested hierarchical creation — subsystems & subdeployments
      case 'subsystems':
        return parentId ? b.getSystemSubsystems(parentId).split('?')[0] : '/systems'
      case 'subdeployments':
        return parentId ? b.getDeploymentSubdeployments(parentId).split('?')[0] : '/deployments'
      default: return `/${toUrlPath(resourceType)}`
    }
  } catch {
    // Fallback to manual nested URLs for Part 2
    if (resourceType === 'datastreams' && parentId) return `/systems/${parentId}/datastreams`
    if (resourceType === 'controlStreams' && parentId) return `/systems/${parentId}/controlstreams`
    if (resourceType === 'observations' && parentId) return `/datastreams/${parentId}/observations`
    if (resourceType === 'commands' && parentId) return `/controlstreams/${parentId}/commands`
    if (resourceType === 'subsystems' && parentId) return `/systems/${parentId}/subsystems`
    if (resourceType === 'subdeployments' && parentId) return `/deployments/${parentId}/subdeployments`
    return `/${toUrlPath(resourceType)}`
  }
}

/**
 * Build the PUT URL for updating a resource.
 */
export function getUpdateUrl(resourceType: string, id: string): string {
  const b = builder.value
  if (!b) return `/${toUrlPath(resourceType)}/${id}`

  try {
    switch (resourceType) {
      case 'systems': return b.updateSystem(id)
      case 'deployments': return b.updateDeployment(id)
      case 'procedures': return b.updateProcedure(id)
      case 'samplingFeatures': return b.updateSamplingFeature(id)
      case 'datastreams': return b.updateDataStream(id)
      case 'observations': return b.updateObservation(id)
      case 'controlStreams': return b.updateControlStream(id)
      case 'commands': return b.updateCommand(id)
      default: return `/${toUrlPath(resourceType)}/${id}`
    }
  } catch {
    return `/${toUrlPath(resourceType)}/${id}`
  }
}

/**
 * Build the DELETE URL for deleting a resource.
 */
export function getDeleteUrl(resourceType: string, id: string): string {
  const b = builder.value
  if (!b) return `/${toUrlPath(resourceType)}/${id}`

  try {
    switch (resourceType) {
      case 'systems': return b.deleteSystem(id)
      case 'deployments': return b.deleteDeployment(id)
      case 'procedures': return b.deleteProcedure(id)
      case 'samplingFeatures': return b.deleteSamplingFeature(id)
      case 'datastreams': return b.deleteDataStream(id)
      case 'observations': return b.deleteObservation(id)
      case 'controlStreams': return b.deleteControlStream(id)
      case 'commands': return b.deleteCommand(id)
      default: return `/${toUrlPath(resourceType)}/${id}`
    }
  } catch {
    return `/${toUrlPath(resourceType)}/${id}`
  }
}

// ========================================
// Nested / Hierarchical Resource URL Helpers
// ========================================

/**
 * Build the list URL for a nested (child) resource under a parent.
 * Maps parentType + relation to the correct builder method.
 *
 * Examples:
 *   getNestedListUrl('systems', 'abc', 'subsystems')      → /systems/abc/subsystems
 *   getNestedListUrl('systems', 'abc', 'datastreams')      → /systems/abc/datastreams
 *   getNestedListUrl('deployments', 'x', 'subdeployments') → /deployments/x/subdeployments
 */
export function getNestedListUrl(
  parentType: string,
  parentId: string,
  relation: string,
  options?: QueryOptions
): string {
  const b = builder.value
  if (!b) return `/${toUrlPath(parentType)}/${parentId}/${relation}`

  try {
    if (parentType === 'systems') {
      switch (relation) {
        case 'subsystems': return b.getSystemSubsystems(parentId, options as SystemQueryOptions)
        case 'datastreams': return b.getSystemDataStreams(parentId, options as DatastreamQueryOptions)
        case 'controlstreams': return b.getSystemControlStreams(parentId, options as ControlStreamQueryOptions)
        case 'samplingFeatures': return b.getSystemSamplingFeatures(parentId, options)
        case 'deployments': return b.getSystemDeployments(parentId, options as DeploymentQueryOptions)
        case 'procedures': return b.getSystemProcedures(parentId, options)
      }
    }
    if (parentType === 'deployments') {
      switch (relation) {
        case 'subdeployments': return b.getDeploymentSubdeployments(parentId, options as DeploymentQueryOptions)
        case 'systems': return b.getDeploymentSystems(parentId, options as SystemQueryOptions)
      }
    }
    if (parentType === 'datastreams') {
      switch (relation) {
        case 'observations': return b.getDataStreamObservations(parentId, options as ObservationQueryOptions)
      }
    }
    if (parentType === 'controlStreams') {
      switch (relation) {
        case 'commands': return b.getControlStreamCommands(parentId, options as CommandQueryOptions)
      }
    }
  } catch {
    // Fall through to manual path
  }
  return `/${toUrlPath(parentType)}/${parentId}/${relation}`
}

// ========================================
// Schema URL Helper
// ========================================

/**
 * Build the URL for a datastream's observation schema.
 * Returns null if the builder is not initialized or the resource is unavailable.
 */
export function getSchemaUrl(datastreamId: string): string | null {
  const b = builder.value
  if (!b) return null
  try {
    return b.getDataStreamSchema(datastreamId)
  } catch {
    return null
  }
}

// ========================================
// Content-Type Helper (backed by library)
// ========================================

/**
 * Returns the correct Accept/Content-Type for a CSAPI resource type.
 * Uses the library's getContentTypeForResource() which maps Part 1 types
 * to application/geo+json and Part 2 types to application/json.
 */
export function getContentType(resourceType: string): string {
  return getContentTypeForResource(resourceType)
}

// ========================================
// Part 2 Typed Parsers
// ========================================

/**
 * Parse a raw Part 2 resource into a typed object using the library's parsers.
 * Returns null for unrecognized types or parse failures.
 *
 * Supported: datastreams, observations, controlStreams, commands, properties
 */
export function parsePart2Resource(resourceType: string, raw: unknown): any | null {
  try {
    switch (resourceType) {
      case 'datastreams': return parseDatastream(raw)
      case 'observations': return parseObservation(raw)
      case 'controlStreams': return parseControlStream(raw)
      case 'commands': return parseCommand(raw)
      case 'properties': return parseProperty(raw)
      default: return null
    }
  } catch {
    return null
  }
}

/**
 * Try to parse a command status from raw JSON.
 * Returns null on failure.
 */
export function tryParseCommandStatus(raw: unknown): any | null {
  try {
    return parseCommandStatus(raw)
  } catch {
    return null
  }
}

// ========================================
// Classification Fallback (for 52North)
// ========================================

/**
 * Classify a feature using featureType first, then endpoint URL path fallback.
 * Solves 52North's featureType:null issue — infers type from the URL.
 */
export function classifyResource(feature: unknown, endpointUrl?: string): string | null {
  const hint = endpointUrl ? inferResourceTypeFromPath(endpointUrl) : null
  return classifyFeature(feature, hint)
}

// ========================================
// Re-exports from the library
// ========================================

export {
  parseCollectionResponse,
  extractCSAPIFeature,
  getCSAPIResourceType,
  classifyFeature,
  inferResourceTypeFromPath,
  parseDatastream,
  parseObservation,
  parseControlStream,
  parseCommand,
  parseCommandStatus,
  parseProperty,
  parseDatastreamSchemaResponse,
  parseSensorML30,
}
export { parseSWEComponent } from '@csapi/ogc-api/csapi/formats/swecommon/parser'
export type { AnyComponent } from '@csapi/ogc-api/csapi/formats/swecommon/types'
export type { CollectionResponse }
