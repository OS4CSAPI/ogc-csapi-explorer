import type { OgcApiCollectionInfo } from '../model.js';
import type { QueryOptions, SystemQueryOptions, DeploymentQueryOptions, ProcedureQueryOptions, SamplingFeatureQueryOptions, PropertyQueryOptions, DatastreamQueryOptions, ObservationQueryOptions, ControlStreamQueryOptions, CommandQueryOptions } from './model.js';
import { CSAPIResourceTypes } from './model.js';
import { EndpointError } from '../../shared/endpoint-error.js';
import {
  encodeResourceId,
  formatDateTimeParameter,
  scanCsapiLinks,
  validateLimit,
  validateBbox,
} from './helpers.js';

/**
 * Builds query URLs for the OGC API - Connected Systems specification.
 *
 * Constructs canonical and nested resource endpoint URLs for all 9 CSAPI
 * resource types (Part 1: systems, deployments, procedures, samplingFeatures,
 * properties; Part 2: datastreams, observations, controlStreams, commands).
 *
 * ## Resource Discovery
 *
 * Available resources are discovered automatically from the collection's link
 * relations. Attempting to build a URL for an unavailable resource throws an
 * {@link EndpointError}. Check `availableResources` to inspect what is available.
 *
 * ## Error Handling
 *
 * All URL-building methods throw {@link EndpointError} when the requested
 * resource type is not available on the collection. Wrap calls in try/catch
 * or check `builder.availableResources.has('systems')` before calling.
 *
 * ```ts
 * try {
 *   const url = builder.getSystems();
 * } catch (e) {
 *   if (e instanceof EndpointError) {
 *     console.warn('Systems not available:', e.message);
 *   }
 * }
 * ```
 *
 * ## Migration from Direct API Access
 *
 * Instead of manually constructing CSAPI URLs:
 * ```ts
 * // Before (manual URL construction):
 * const url = `${baseUrl}/collections/${collectionId}/systems?limit=50&bbox=-180,-90,180,90`;
 *
 * // After (using CSAPIQueryBuilder):
 * const endpoint = await new OgcApiEndpoint(baseUrl);
 * const builder = await endpoint.csapi(collectionId);
 * const url = builder.getSystems({ limit: 50, bbox: [-180, -90, 180, 90] });
 * ```
 *
 * The builder handles URL encoding, parameter validation, resource
 * availability checks, and supports both collection-scoped and
 * root-level API resource URLs automatically.
 *
 * @example Complete workflow — list, filter, and navigate CSAPI resources:
 * ```ts
 * import { OgcApiEndpoint } from '@AugmentedGeo/ogc-client';
 *
 * const endpoint = await new OgcApiEndpoint('https://api.example.com');
 * const builder = await endpoint.csapi('weather-stations');
 *
 * // List systems with spatial and text filters
 * const systemsUrl = builder.getSystems({
 *   bbox: [-105, 39, -104, 40],
 *   q: 'temperature',
 *   limit: 25,
 * });
 *
 * // Get a specific system
 * const systemUrl = builder.getSystem('sys-001');
 *
 * // List observations for a datastream with temporal filter
 * const obsUrl = builder.getObservationsForDatastream('ds-001', {
 *   phenomenonTime: { start: new Date('2024-01-01') },
 *   limit: 100,
 * });
 *
 * // Create a new system (returns the POST URL)
 * const createUrl = builder.createSystem();
 * ```
 *
 * @see https://docs.ogc.org/is/23-001/23-001.html — OGC API - Connected Systems Part 1
 * @see https://docs.ogc.org/is/23-002/23-002.html — OGC API - Connected Systems Part 2
 */
export default class CSAPIQueryBuilder {
  /**
   * The set of CSAPI resource types available on this collection,
   * discovered from the collection's link relations.
   */
  public readonly availableResources: Set<string>;

  /** Base URL for resource endpoints, derived from collection links. */
  private baseUrl: string;

  /**
   * Optional map of resource type → absolute URL, supplied when the
   * server advertises top-level (non-collection-scoped) resource URLs
   * in the root API document. When present, `buildResourceUrl()` uses
   * these absolute URLs instead of computing paths relative to the
   * collection self link.
   */
  private resourceUrls_: Map<string, string>;

  /**
   * @param collection_ - The OGC API collection metadata object.
   *   Must contain a `links` array; CSAPI resource availability is
   *   discovered from link relations matching `ogc-cs:{resourceType}`,
   *   plain resource names, or `items` links with resource hrefs.
   * @param resourceUrls - Optional map of resource type names to absolute
   *   URLs. When provided (e.g., from the root API document), these URLs
   *   are used as the base for resource endpoints instead of the
   *   collection-scoped self link. This supports servers that expose
   *   CSAPI resources at the API root (e.g., `/api/systems`) rather than
   *   under a collection path (e.g., `/collections/{id}/systems`).
   * @see https://docs.ogc.org/is/23-001/23-001.html
   */
  constructor(
    private collection_: OgcApiCollectionInfo,
    resourceUrls?: Map<string, string>
  ) {
    this.resourceUrls_ = resourceUrls ?? new Map();
    this.baseUrl = this.extractBaseUrl();
    this.availableResources = this.extractAvailableResources();
  }

  // ========================================
  // PRIVATE HELPERS
  // ========================================

  /**
   * Extracts the base URL for CSAPI resource endpoints from collection links.
   * Looks for a self link or falls back to the first available href.
   */
  private extractBaseUrl(): string {
    const links = this.collection_.links;
    if (!Array.isArray(links) || links.length === 0) {
      return '';
    }

    const selfLink = links.find(
      (l: { rel?: string; href?: string }) => l.rel === 'self'
    );
    if (selfLink?.href) {
      return selfLink.href.replace(/\/$/, '');
    }

    // Fall back to first link with an href
    const first = links.find(
      (l: { href?: string }) => typeof l.href === 'string'
    );
    return first?.href?.replace(/\/$/, '') ?? '';
  }

  /**
   * Discovers available CSAPI resource types from collection link relations.
   *
   * Recognizes three link relation conventions, in priority order:
   *
   * 1. **`ogc-cs:` prefixed** — `rel: "ogc-cs:systems"` → resource `"systems"`
   * 2. **Plain resource name** — `rel: "systems"` where the value is a known
   *    {@link CSAPIResourceTypes} member → resource `"systems"`
   * 3. **`items` with resource href** — `rel: "items"` where the `href` path
   *    ends with a known resource type name → resource extracted from href
   *
   * All three conventions populate the same Set. Duplicate entries are
   * deduplicated automatically.
   *
   * @returns Set of available resource type names (e.g., 'systems', 'datastreams').
   * @see https://docs.ogc.org/is/23-001/23-001.html
   */
  private extractAvailableResources(): Set<string> {
    const links = this.collection_.links;
    if (!Array.isArray(links)) {
      return new Set<string>();
    }
    return new Set(scanCsapiLinks(links).keys());
  }

  /**
   * Core URL construction helper.
   * Handles canonical, nested, and top-level resource endpoints.
   *
   * If the constructor received a `resourceUrls` map containing an
   * absolute URL for the given `resourceType`, that URL is used as the
   * base (top-level pattern). Otherwise, the URL is built relative to
   * the collection self link (collection-scoped pattern).
   *
   * @param resourceType - Resource type (systems, deployments, etc.)
   * @param id - Optional resource ID.
   * @param subPath - Optional sub-path (subsystems, datastreams, etc.)
   * @param options - Query parameters.
   * @returns Fully constructed URL string.
   * @see https://docs.ogc.org/is/23-001/23-001.html
   */
  private buildResourceUrl(
    resourceType: string,
    id?: string,
    subPath?: string,
    options?: QueryOptions
  ): string {
    // Use the absolute resource URL when available (top-level pattern),
    // otherwise fall back to collection-scoped base URL.
    const topLevelUrl = this.resourceUrls_.get(resourceType);
    const resourceBase = topLevelUrl
      ? topLevelUrl.replace(/\/+$/, '')
      : `${this.baseUrl}/${resourceType}`;
    let url = resourceBase;
    if (id) url += `/${encodeResourceId(id)}`;
    if (subPath) url += `/${subPath}`;
    return url + this.buildQueryString(options);
  }

  /**
   * Serializes query options into a URL query string.
   * Handles undefined/null skipping, array joining, temporal formatting,
   * and bbox validation.
   * @param options - Query parameter object.
   * @returns Query string with leading '?', or empty string if no params.
   */
  /**
   * Temporal parameter keys that require ISO 8601 date/interval formatting.
   * Used by `buildQueryString` to detect parameters needing `formatDateTimeParameter`.
   * @see https://docs.ogc.org/is/23-001/23-001.html
   * @see https://docs.ogc.org/is/23-002/23-002.html
   */
  private static readonly TEMPORAL_KEYS: ReadonlySet<string> = new Set([
    'datetime', 'phenomenonTime', 'resultTime', 'issueTime', 'executionTime',
  ]);

  private buildQueryString(options?: QueryOptions): string {
    if (!options) return '';
    const params = new URLSearchParams();

    for (const [key, value] of Object.entries(options)) {
      if (value === undefined || value === null) {
        continue;
      }

      if (key === 'bbox') {
        validateBbox(value);
        params.append(key, value.join(','));
      } else if (CSAPIQueryBuilder.TEMPORAL_KEYS.has(key)) {
        params.append(key, formatDateTimeParameter(value));
      } else if (key === 'limit') {
        validateLimit(value);
        params.append(key, String(value));
      } else if (Array.isArray(value)) {
        // Use plain join — URLSearchParams.append() handles percent-encoding.
        // Previously used encodeArrayParameter() here, which pre-encoded values
        // before URLSearchParams encoded them again (double-encoding bug F5).
        params.append(key, value.join(','));
      } else {
        params.append(key, String(value));
      }
    }

    const queryString = params.toString();
    return queryString ? `?${queryString}` : '';
  }

  /**
   * Validates that a resource type is available on this collection.
   * @param resourceType - The resource type to validate.
   * @throws {EndpointError} If the resource type is not available.
   */
  private assertResourceAvailable(resourceType: string): void {
    if (!this.availableResources.has(resourceType)) {
      throw new EndpointError(
        `Collection '${this.collection_.id}' does not support '${resourceType}' resource. ` +
          `Available resources: ${Array.from(this.availableResources).join(', ')}`
      );
    }
  }

  // ========================================
  // SYSTEMS METHODS
  // ========================================

  /**
   * Returns the URL for listing systems.
   *
   * @param options - Optional query parameters for filtering systems.
   * @returns URL string for the systems list endpoint.
   * @throws {EndpointError} If 'systems' is not available on this collection.
   *
   * @example
   * ```ts
   * const url = builder.getSystems({ limit: 10 });
   * // => "https://example.com/collections/iot/systems?limit=10"
   * ```
   *
   * @see https://docs.ogc.org/is/23-001/23-001.html#_system_resources
   */
  getSystems(options?: SystemQueryOptions): string {
    this.assertResourceAvailable('systems');
    return this.buildResourceUrl('systems', undefined, undefined, options);
  }

  /**
   * Returns the URL for retrieving a single system by ID.
   *
   * @param id - The system resource identifier.
   * @param options - Optional query parameters.
   * @returns URL string for the individual system endpoint.
   * @throws {EndpointError} If 'systems' is not available on this collection.
   *
   * @example
   * ```ts
   * const url = builder.getSystem('abc123');
   * // => "https://example.com/collections/iot/systems/abc123"
   * ```
   *
   * @see https://docs.ogc.org/is/23-001/23-001.html#_system_resources
   */
  getSystem(id: string, options?: QueryOptions): string {
    this.assertResourceAvailable('systems');
    return this.buildResourceUrl('systems', id, undefined, options);
  }

  /**
   * Returns the URL for creating a new system (POST target).
   *
   * @returns URL string for the systems collection endpoint.
   * @throws {EndpointError} If 'systems' is not available on this collection.
   *
   * @example
   * ```ts
   * const url = builder.createSystem();
   * // POST to => "https://example.com/collections/iot/systems"
   * ```
   *
   * @see https://docs.ogc.org/is/23-001/23-001.html#_system_resources
   */
  createSystem(): string {
    this.assertResourceAvailable('systems');
    return this.buildResourceUrl('systems');
  }

  /**
   * Returns the URL for updating an existing system (PUT target).
   *
   * @param id - The system resource identifier to update.
   * @returns URL string for the individual system endpoint.
   * @throws {EndpointError} If 'systems' is not available on this collection.
   *
   * @example
   * ```ts
   * const url = builder.updateSystem('abc123');
   * // PUT to => "https://example.com/collections/iot/systems/abc123"
   * ```
   *
   * @see https://docs.ogc.org/is/23-001/23-001.html#_system_resources
   */
  updateSystem(id: string): string {
    this.assertResourceAvailable('systems');
    return this.buildResourceUrl('systems', id);
  }

  /**
   * Returns the URL for deleting a system (DELETE target).
   *
   * @param id - The system resource identifier to delete.
   * @returns URL string for the individual system endpoint.
   * @throws {EndpointError} If 'systems' is not available on this collection.
   *
   * @example
   * ```ts
   * const url = builder.deleteSystem('abc123');
   * // DELETE to => "https://example.com/collections/iot/systems/abc123"
   * ```
   *
   * @see https://docs.ogc.org/is/23-001/23-001.html#_system_resources
   */
  deleteSystem(id: string): string {
    this.assertResourceAvailable('systems');
    return this.buildResourceUrl('systems', id);
  }

  /**
   * Returns the URL for retrieving a system's version history.
   *
   * @param id - The system resource identifier.
   * @param options - Optional query parameters for filtering history entries.
   * @returns URL string for the system history endpoint.
   * @throws {EndpointError} If 'systems' is not available on this collection.
   *
   * @example
   * ```ts
   * const url = builder.getSystemHistory('abc123', { limit: 5 });
   * // => "https://example.com/collections/iot/systems/abc123/history?limit=5"
   * ```
   *
   * @see https://docs.ogc.org/is/23-001/23-001.html#_system_history
   */
  getSystemHistory(id: string, options?: QueryOptions): string {
    this.assertResourceAvailable('systems');
    return this.buildResourceUrl('systems', id, 'history', options);
  }

  /**
   * Returns the URL for listing subsystems of a system.
   *
   * @param id - The parent system resource identifier.
   * @param options - Optional query parameters. Supports `recursive` parameter
   *   to include nested subsystems at all levels.
   * @returns URL string for the system's subsystems endpoint.
   * @throws {EndpointError} If 'systems' is not available on this collection.
   *
   * @example
   * ```ts
   * const url = builder.getSystemSubsystems('abc123', { recursive: true });
   * // => "https://example.com/collections/iot/systems/abc123/subsystems?recursive=true"
   * ```
   *
   * @see https://docs.ogc.org/is/23-001/23-001.html#_system_resources
   */
  getSystemSubsystems(id: string, options?: SystemQueryOptions): string {
    this.assertResourceAvailable('systems');
    return this.buildResourceUrl('systems', id, 'subsystems', options);
  }

  /**
   * Returns the URL for listing datastreams associated with a system.
   *
   * @param id - The system resource identifier.
   * @param options - Optional query parameters for filtering datastreams.
   * @returns URL string for the system's datastreams endpoint.
   * @throws {EndpointError} If 'systems' is not available on this collection.
   *
   * @example
   * ```ts
   * const url = builder.getSystemDataStreams('abc123');
   * // => "https://example.com/collections/iot/systems/abc123/datastreams"
   * ```
   *
   * @see https://docs.ogc.org/is/23-002/23-002.html#_datastream_resources
   */
  getSystemDataStreams(id: string, options?: QueryOptions): string {
    this.assertResourceAvailable('systems');
    return this.buildResourceUrl('systems', id, 'datastreams', options);
  }

  /**
   * Returns the URL for listing control streams associated with a system.
   *
   * @param id - The system resource identifier.
   * @param options - Optional query parameters for filtering control streams.
   * @returns URL string for the system's control streams endpoint.
   * @throws {EndpointError} If 'systems' is not available on this collection.
   *
   * @example
   * ```ts
   * const url = builder.getSystemControlStreams('abc123');
   * // => "https://example.com/collections/iot/systems/abc123/controlstreams"
   * ```
   *
   * @see https://docs.ogc.org/is/23-002/23-002.html#_controlstream_resources
   */
  getSystemControlStreams(id: string, options?: QueryOptions): string {
    this.assertResourceAvailable('systems');
    return this.buildResourceUrl('systems', id, 'controlstreams', options);
  }

  /**
   * Returns the URL for listing sampling features associated with a system.
   *
   * @param id - The system resource identifier.
   * @param options - Optional query parameters for filtering sampling features.
   * @returns URL string for the system's sampling features endpoint.
   * @throws {EndpointError} If 'systems' is not available on this collection.
   *
   * @example
   * ```ts
   * const url = builder.getSystemSamplingFeatures('abc123');
   * // => "https://example.com/collections/iot/systems/abc123/samplingFeatures"
   * ```
   *
   * @see https://docs.ogc.org/is/23-001/23-001.html#_sampling_feature_resources
   */
  getSystemSamplingFeatures(id: string, options?: QueryOptions): string {
    this.assertResourceAvailable('systems');
    return this.buildResourceUrl('systems', id, 'samplingFeatures', options);
  }

  /**
   * Returns the URL for listing deployments associated with a system.
   *
   * @param id - The system resource identifier.
   * @param options - Optional query parameters for filtering deployments.
   * @returns URL string for the system's deployments endpoint.
   * @throws {EndpointError} If 'systems' is not available on this collection.
   *
   * @example
   * ```ts
   * const url = builder.getSystemDeployments('abc123');
   * // => "https://example.com/collections/iot/systems/abc123/deployments"
   * ```
   *
   * @see https://docs.ogc.org/is/23-001/23-001.html#_deployment_resources
   */
  getSystemDeployments(id: string, options?: QueryOptions): string {
    this.assertResourceAvailable('systems');
    return this.buildResourceUrl('systems', id, 'deployments', options);
  }

  /**
   * Returns the URL for listing procedures associated with a system.
   *
   * @param id - The system resource identifier.
   * @param options - Optional query parameters for filtering procedures.
   * @returns URL string for the system's procedures endpoint.
   * @throws {EndpointError} If 'systems' is not available on this collection.
   *
   * @example
   * ```ts
   * const url = builder.getSystemProcedures('abc123');
   * // => "https://example.com/collections/iot/systems/abc123/procedures"
   * ```
   *
   * @see https://docs.ogc.org/is/23-001/23-001.html#_procedure_resources
   */
  getSystemProcedures(id: string, options?: QueryOptions): string {
    this.assertResourceAvailable('systems');
    return this.buildResourceUrl('systems', id, 'procedures', options);
  }

  // ========================================
  // DEPLOYMENTS METHODS
  // ========================================

  /**
   * Returns the URL for querying the deployments collection.
   *
   * @param options - Optional query parameters for filtering, pagination, bbox,
   *   datetime, sorting, and deployment-specific filters.
   * @returns URL string for the deployments collection endpoint.
   * @throws {EndpointError} If 'deployments' is not available on this collection.
   *
   * @example
   * ```ts
   * const url = builder.getDeployments({ limit: 10, bbox: [-180, -90, 180, 90] });
   * // => "https://example.com/collections/iot/deployments?limit=10&bbox=-180%2C-90%2C180%2C90"
   * ```
   *
   * @see https://docs.ogc.org/is/23-001/23-001.html#_deployment_resources
   */
  getDeployments(options?: DeploymentQueryOptions): string {
    this.assertResourceAvailable('deployments');
    return this.buildResourceUrl('deployments', undefined, undefined, options);
  }

  /**
   * Returns the URL for retrieving a single deployment by ID.
   *
   * @param id - The deployment resource identifier.
   * @param options - Optional query parameters.
   * @returns URL string for the individual deployment endpoint.
   * @throws {EndpointError} If 'deployments' is not available on this collection.
   *
   * @example
   * ```ts
   * const url = builder.getDeployment('dep-001');
   * // => "https://example.com/collections/iot/deployments/dep-001"
   * ```
   *
   * @see https://docs.ogc.org/is/23-001/23-001.html#_deployment_resources
   */
  getDeployment(id: string, options?: QueryOptions): string {
    this.assertResourceAvailable('deployments');
    return this.buildResourceUrl('deployments', id, undefined, options);
  }

  /**
   * Returns the URL for creating a new deployment (POST target).
   *
   * @returns URL string for the deployments collection endpoint.
   * @throws {EndpointError} If 'deployments' is not available on this collection.
   *
   * @example
   * ```ts
   * const url = builder.createDeployment();
   * // POST to => "https://example.com/collections/iot/deployments"
   * ```
   *
   * @see https://docs.ogc.org/is/23-001/23-001.html#_deployment_resources
   */
  createDeployment(): string {
    this.assertResourceAvailable('deployments');
    return this.buildResourceUrl('deployments');
  }

  /**
   * Returns the URL for updating an existing deployment (PUT target).
   *
   * @param id - The deployment resource identifier to update.
   * @returns URL string for the individual deployment endpoint.
   * @throws {EndpointError} If 'deployments' is not available on this collection.
   *
   * @example
   * ```ts
   * const url = builder.updateDeployment('dep-001');
   * // PUT to => "https://example.com/collections/iot/deployments/dep-001"
   * ```
   *
   * @see https://docs.ogc.org/is/23-001/23-001.html#_deployment_resources
   */
  updateDeployment(id: string): string {
    this.assertResourceAvailable('deployments');
    return this.buildResourceUrl('deployments', id);
  }

  /**
   * Returns the URL for deleting a deployment (DELETE target).
   *
   * @param id - The deployment resource identifier to delete.
   * @returns URL string for the individual deployment endpoint.
   * @throws {EndpointError} If 'deployments' is not available on this collection.
   *
   * @example
   * ```ts
   * const url = builder.deleteDeployment('dep-001');
   * // DELETE to => "https://example.com/collections/iot/deployments/dep-001"
   * ```
   *
   * @see https://docs.ogc.org/is/23-001/23-001.html#_deployment_resources
   */
  deleteDeployment(id: string): string {
    this.assertResourceAvailable('deployments');
    return this.buildResourceUrl('deployments', id);
  }

  /**
   * Returns the URL for listing subdeployments of a deployment.
   *
   * @param id - The parent deployment resource identifier.
   * @param options - Optional query parameters. Supports `recursive` parameter
   *   to include nested subdeployments at all levels.
   * @returns URL string for the deployment's subdeployments endpoint.
   * @throws {EndpointError} If 'deployments' is not available on this collection.
   *
   * @example
   * ```ts
   * const url = builder.getDeploymentSubdeployments('dep-001', { recursive: true });
   * // => "https://example.com/collections/iot/deployments/dep-001/subdeployments?recursive=true"
   * ```
   *
   * @see https://docs.ogc.org/is/23-001/23-001.html#_deployment_resources
   */
  getDeploymentSubdeployments(id: string, options?: DeploymentQueryOptions): string {
    this.assertResourceAvailable('deployments');
    return this.buildResourceUrl('deployments', id, 'subdeployments', options);
  }

  /**
   * Returns the URL for listing systems associated with a deployment.
   *
   * @param id - The deployment resource identifier.
   * @param options - Optional query parameters for filtering systems.
   * @returns URL string for the deployment's systems endpoint.
   * @throws {EndpointError} If 'deployments' is not available on this collection.
   *
   * @example
   * ```ts
   * const url = builder.getDeploymentSystems('dep-001');
   * // => "https://example.com/collections/iot/deployments/dep-001/systems"
   * ```
   *
   * @see https://docs.ogc.org/is/23-001/23-001.html#_deployment_resources
   */
  getDeploymentSystems(id: string, options?: QueryOptions): string {
    this.assertResourceAvailable('deployments');
    return this.buildResourceUrl('deployments', id, 'systems', options);
  }

  /**
   * Returns the URL for retrieving a deployment's version history.
   *
   * @param id - The deployment resource identifier.
   * @param options - Optional query parameters for filtering history entries.
   * @returns URL string for the deployment history endpoint.
   * @throws {EndpointError} If 'deployments' is not available on this collection.
   *
   * @example
   * ```ts
   * const url = builder.getDeploymentHistory('dep-001', { limit: 5 });
   * // => "https://example.com/collections/iot/deployments/dep-001/history?limit=5"
   * ```
   *
   * @see https://docs.ogc.org/is/23-001/23-001.html#_deployment_history
   */
  getDeploymentHistory(id: string, options?: QueryOptions): string {
    this.assertResourceAvailable('deployments');
    return this.buildResourceUrl('deployments', id, 'history', options);
  }

  // ========================================
  // PROCEDURES METHODS
  // ========================================

  /**
   * Returns the URL for listing procedures.
   *
   * @param options - Optional query parameters for filtering procedures.
   *   Procedures support: `id`, `uid`, `q`, `limit`, `offset`, `f`.
   *   Procedures do NOT support `bbox`, `datetime`, `parent`, or `recursive`.
   * @returns URL string for the procedures list endpoint.
   * @throws {EndpointError} If 'procedures' is not available on this collection.
   *
   * @example
   * ```ts
   * const url = builder.getProcedures({ limit: 10, q: 'thermometer' });
   * // => "https://example.com/collections/iot/procedures?limit=10&q=thermometer"
   * ```
   *
   * @see https://docs.ogc.org/is/23-001/23-001.html#_procedure_resources
   */
  getProcedures(options?: ProcedureQueryOptions): string {
    this.assertResourceAvailable('procedures');
    return this.buildResourceUrl('procedures', undefined, undefined, options);
  }

  /**
   * Returns the URL for retrieving a single procedure by ID.
   *
   * @param id - The procedure resource identifier.
   * @param options - Optional query parameters.
   * @returns URL string for the individual procedure endpoint.
   * @throws {EndpointError} If 'procedures' is not available on this collection.
   *
   * @example
   * ```ts
   * const url = builder.getProcedure('proc-001');
   * // => "https://example.com/collections/iot/procedures/proc-001"
   * ```
   *
   * @see https://docs.ogc.org/is/23-001/23-001.html#_procedure_resources
   */
  getProcedure(id: string, options?: QueryOptions): string {
    this.assertResourceAvailable('procedures');
    return this.buildResourceUrl('procedures', id, undefined, options);
  }

  /**
   * Returns the URL for creating a new procedure (POST target).
   *
   * @returns URL string for the procedures collection endpoint.
   * @throws {EndpointError} If 'procedures' is not available on this collection.
   *
   * @example
   * ```ts
   * const url = builder.createProcedure();
   * // POST to => "https://example.com/collections/iot/procedures"
   * ```
   *
   * @see https://docs.ogc.org/is/23-001/23-001.html#_procedure_resources
   */
  createProcedure(): string {
    this.assertResourceAvailable('procedures');
    return this.buildResourceUrl('procedures');
  }

  /**
   * Returns the URL for updating an existing procedure (PUT target).
   *
   * @param id - The procedure resource identifier to update.
   * @returns URL string for the individual procedure endpoint.
   * @throws {EndpointError} If 'procedures' is not available on this collection.
   *
   * @example
   * ```ts
   * const url = builder.updateProcedure('proc-001');
   * // PUT to => "https://example.com/collections/iot/procedures/proc-001"
   * ```
   *
   * @see https://docs.ogc.org/is/23-001/23-001.html#_procedure_resources
   */
  updateProcedure(id: string): string {
    this.assertResourceAvailable('procedures');
    return this.buildResourceUrl('procedures', id);
  }

  /**
   * Returns the URL for deleting a procedure (DELETE target).
   *
   * @param id - The procedure resource identifier to delete.
   * @returns URL string for the individual procedure endpoint.
   * @throws {EndpointError} If 'procedures' is not available on this collection.
   *
   * @example
   * ```ts
   * const url = builder.deleteProcedure('proc-001');
   * // DELETE to => "https://example.com/collections/iot/procedures/proc-001"
   * ```
   *
   * @see https://docs.ogc.org/is/23-001/23-001.html#_procedure_resources
   */
  deleteProcedure(id: string): string {
    this.assertResourceAvailable('procedures');
    return this.buildResourceUrl('procedures', id);
  }

  /**
   * Returns the URL for listing systems that implement a procedure.
   *
   * @param id - The procedure resource identifier.
   * @param options - Optional query parameters for filtering systems.
   * @returns URL string for the procedure's systems endpoint.
   * @throws {EndpointError} If 'procedures' is not available on this collection.
   *
   * @example
   * ```ts
   * const url = builder.getProcedureSystems('proc-001', { limit: 5 });
   * // => "https://example.com/collections/iot/procedures/proc-001/systems?limit=5"
   * ```
   *
   * @see https://docs.ogc.org/is/23-001/23-001.html#_procedure_resources
   */
  getProcedureSystems(id: string, options?: QueryOptions): string {
    this.assertResourceAvailable('procedures');
    return this.buildResourceUrl('procedures', id, 'systems', options);
  }

  /**
   * Returns the URL for listing datastreams associated with a procedure.
   *
   * @param id - The procedure resource identifier.
   * @param options - Optional query parameters for filtering datastreams.
   * @returns URL string for the procedure's datastreams endpoint.
   * @throws {EndpointError} If 'procedures' is not available on this collection.
   *
   * @example
   * ```ts
   * const url = builder.getProcedureDataStreams('proc-001');
   * // => "https://example.com/collections/iot/procedures/proc-001/datastreams"
   * ```
   *
   * @see https://docs.ogc.org/is/23-002/23-002.html#_datastream_resources
   */
  getProcedureDataStreams(id: string, options?: QueryOptions): string {
    this.assertResourceAvailable('procedures');
    return this.buildResourceUrl('procedures', id, 'datastreams', options);
  }

  /**
   * Returns the URL for retrieving a procedure's version history.
   *
   * @param id - The procedure resource identifier.
   * @param options - Optional query parameters for filtering history entries.
   * @returns URL string for the procedure history endpoint.
   * @throws {EndpointError} If 'procedures' is not available on this collection.
   *
   * @example
   * ```ts
   * const url = builder.getProcedureHistory('proc-001', { limit: 5 });
   * // => "https://example.com/collections/iot/procedures/proc-001/history?limit=5"
   * ```
   *
   * @see https://docs.ogc.org/is/23-001/23-001.html#_procedure_history
   */
  getProcedureHistory(id: string, options?: QueryOptions): string {
    this.assertResourceAvailable('procedures');
    return this.buildResourceUrl('procedures', id, 'history', options);
  }

  // ========================================
  // SAMPLING FEATURES METHODS
  // ========================================

  /**
   * Returns the URL for listing sampling features.
   *
   * @param options - Optional query parameters for filtering sampling features.
   *   Sampling features support: `id`, `uid`, `q`, `bbox`, `datetime`, `limit`, `offset`, `f`.
   *   Sampling features do NOT support `parent`, `recursive`, or cursor-based pagination.
   * @returns URL string for the sampling features list endpoint.
   * @throws {EndpointError} If 'samplingFeatures' is not available on this collection.
   *
   * @example
   * ```ts
   * const url = builder.getSamplingFeatures({ bbox: [-180, -90, 180, 90], limit: 20 });
   * // => "https://example.com/collections/iot/samplingFeatures?bbox=-180%2C-90%2C180%2C90&limit=20"
   * ```
   *
   * @see https://docs.ogc.org/is/23-001/23-001.html#_sampling_feature_resources
   */
  getSamplingFeatures(options?: SamplingFeatureQueryOptions): string {
    this.assertResourceAvailable('samplingFeatures');
    return this.buildResourceUrl('samplingFeatures', undefined, undefined, options);
  }

  /**
   * Returns the URL for retrieving a single sampling feature by ID.
   *
   * @param id - The sampling feature resource identifier.
   * @param options - Optional query parameters.
   * @returns URL string for the individual sampling feature endpoint.
   * @throws {EndpointError} If 'samplingFeatures' is not available on this collection.
   *
   * @example
   * ```ts
   * const url = builder.getSamplingFeature('sf-001');
   * // => "https://example.com/collections/iot/samplingFeatures/sf-001"
   * ```
   *
   * @see https://docs.ogc.org/is/23-001/23-001.html#_sampling_feature_resources
   */
  getSamplingFeature(id: string, options?: QueryOptions): string {
    this.assertResourceAvailable('samplingFeatures');
    return this.buildResourceUrl('samplingFeatures', id, undefined, options);
  }

  /**
   * Returns the URL for creating a new sampling feature (POST target).
   *
   * @returns URL string for the sampling features collection endpoint.
   * @throws {EndpointError} If 'samplingFeatures' is not available on this collection.
   *
   * @example
   * ```ts
   * const url = builder.createSamplingFeature();
   * // POST to => "https://example.com/collections/iot/samplingFeatures"
   * ```
   *
   * @see https://docs.ogc.org/is/23-001/23-001.html#_sampling_feature_resources
   */
  createSamplingFeature(): string {
    this.assertResourceAvailable('samplingFeatures');
    return this.buildResourceUrl('samplingFeatures');
  }

  /**
   * Returns the URL for updating an existing sampling feature (PUT target).
   *
   * @param id - The sampling feature resource identifier to update.
   * @returns URL string for the individual sampling feature endpoint.
   * @throws {EndpointError} If 'samplingFeatures' is not available on this collection.
   *
   * @example
   * ```ts
   * const url = builder.updateSamplingFeature('sf-001');
   * // PUT to => "https://example.com/collections/iot/samplingFeatures/sf-001"
   * ```
   *
   * @see https://docs.ogc.org/is/23-001/23-001.html#_sampling_feature_resources
   */
  updateSamplingFeature(id: string): string {
    this.assertResourceAvailable('samplingFeatures');
    return this.buildResourceUrl('samplingFeatures', id);
  }

  /**
   * Returns the URL for deleting a sampling feature (DELETE target).
   *
   * @param id - The sampling feature resource identifier to delete.
   * @returns URL string for the individual sampling feature endpoint.
   * @throws {EndpointError} If 'samplingFeatures' is not available on this collection.
   *
   * @example
   * ```ts
   * const url = builder.deleteSamplingFeature('sf-001');
   * // DELETE to => "https://example.com/collections/iot/samplingFeatures/sf-001"
   * ```
   *
   * @see https://docs.ogc.org/is/23-001/23-001.html#_sampling_feature_resources
   */
  deleteSamplingFeature(id: string): string {
    this.assertResourceAvailable('samplingFeatures');
    return this.buildResourceUrl('samplingFeatures', id);
  }

  /**
   * Returns the URL for listing systems associated with a sampling feature.
   *
   * @param id - The sampling feature resource identifier.
   * @param options - Optional query parameters for filtering systems.
   * @returns URL string for the sampling feature's systems endpoint.
   * @throws {EndpointError} If 'samplingFeatures' is not available on this collection.
   *
   * @example
   * ```ts
   * const url = builder.getSamplingFeatureSystems('sf-001', { limit: 5 });
   * // => "https://example.com/collections/iot/samplingFeatures/sf-001/systems?limit=5"
   * ```
   *
   * @see https://docs.ogc.org/is/23-001/23-001.html#_sampling_feature_resources
   */
  getSamplingFeatureSystems(id: string, options?: QueryOptions): string {
    this.assertResourceAvailable('samplingFeatures');
    return this.buildResourceUrl('samplingFeatures', id, 'systems', options);
  }

  /**
   * Returns the URL for listing observations associated with a sampling feature.
   *
   * This is a Part 2 cross-reference endpoint linking Part 1 sampling features
   * to Part 2 observation data.
   *
   * @param id - The sampling feature resource identifier.
   * @param options - Optional query parameters for filtering observations.
   * @returns URL string for the sampling feature's observations endpoint.
   * @throws {EndpointError} If 'samplingFeatures' is not available on this collection.
   *
   * @example
   * ```ts
   * const url = builder.getSamplingFeatureObservations('sf-001');
   * // => "https://example.com/collections/iot/samplingFeatures/sf-001/observations"
   * ```
   *
   * @see https://docs.ogc.org/is/23-002/23-002.html#_observation_resources
   */
  getSamplingFeatureObservations(id: string, options?: QueryOptions): string {
    this.assertResourceAvailable('samplingFeatures');
    return this.buildResourceUrl('samplingFeatures', id, 'observations', options);
  }

  /**
   * Returns the URL for retrieving a sampling feature's version history.
   *
   * @param id - The sampling feature resource identifier.
   * @param options - Optional query parameters for filtering history entries.
   * @returns URL string for the sampling feature history endpoint.
   * @throws {EndpointError} If 'samplingFeatures' is not available on this collection.
   *
   * @example
   * ```ts
   * const url = builder.getSamplingFeatureHistory('sf-001', { limit: 5 });
   * // => "https://example.com/collections/iot/samplingFeatures/sf-001/history?limit=5"
   * ```
   *
   * @see https://docs.ogc.org/is/23-001/23-001.html#_sampling_feature_history
   */
  getSamplingFeatureHistory(id: string, options?: QueryOptions): string {
    this.assertResourceAvailable('samplingFeatures');
    return this.buildResourceUrl('samplingFeatures', id, 'history', options);
  }

  // ========================================
  // PROPERTIES METHODS
  // ========================================

  /**
   * Returns the URL for listing properties.
   *
   * Properties define the observable or controllable quantities that systems
   * can measure or actuate (e.g., temperature, pressure, valve position).
   * Properties are the only Part 1 resource that is **not** a GeoJSON Feature;
   * responses use a plain JSON collection with `items` (not `features`).
   *
   * Properties are **read-only** — there are no create, update, or delete
   * endpoints for Properties in the CSAPI specification.
   *
   * @param options - Optional query parameters for filtering properties.
   *   Properties support: `system`, `baseProperty`, `id`, `uid`, `q`,
   *   property filters, `limit`, `offset`, `f`, `sortBy`, `sortOrder`.
   *   Properties do NOT support `bbox` or `datetime`.
   * @returns URL string for the properties list endpoint.
   * @throws {EndpointError} If 'properties' is not available on this collection.
   *
   * @example
   * ```ts
   * const url = builder.getProperties({ q: 'temperature', limit: 10 });
   * // => "https://example.com/collections/iot/properties?q=temperature&limit=10"
   * ```
   *
   * @see https://docs.ogc.org/is/23-001/23-001.html#_property_resources
   */
  getProperties(options?: PropertyQueryOptions): string {
    this.assertResourceAvailable('properties');
    return this.buildResourceUrl('properties', undefined, undefined, options);
  }

  /**
   * Returns the URL for retrieving a single property by ID.
   *
   * Properties are the only Part 1 resource that is **not** a GeoJSON Feature;
   * the response is a plain JSON object (not a GeoJSON Feature).
   *
   * @param id - The property resource identifier.
   * @param options - Optional query parameters (e.g., `f` for format).
   * @returns URL string for the individual property endpoint.
   * @throws {EndpointError} If 'properties' is not available on this collection.
   *
   * @example
   * ```ts
   * const url = builder.getProperty('temperature-01');
   * // => "https://example.com/collections/iot/properties/temperature-01"
   * ```
   *
   * @see https://docs.ogc.org/is/23-001/23-001.html#_property_resources
   */
  getProperty(id: string, options?: QueryOptions): string {
    this.assertResourceAvailable('properties');
    return this.buildResourceUrl('properties', id, undefined, options);
  }

  /**
   * Returns the URL for listing systems that observe or actuate a property.
   *
   * @param id - The property resource identifier.
   * @param options - Optional query parameters for filtering systems.
   * @returns URL string for the property's systems endpoint.
   * @throws {EndpointError} If 'properties' is not available on this collection.
   *
   * @example
   * ```ts
   * const url = builder.getPropertySystems('temperature-01', { limit: 5 });
   * // => "https://example.com/collections/iot/properties/temperature-01/systems?limit=5"
   * ```
   *
   * @see https://docs.ogc.org/is/23-001/23-001.html#_property_resources
   */
  getPropertySystems(id: string, options?: QueryOptions): string {
    this.assertResourceAvailable('properties');
    return this.buildResourceUrl('properties', id, 'systems', options);
  }

  /**
   * Returns the URL for listing datastreams associated with a property.
   *
   * This is a Part 2 cross-reference endpoint linking Part 1 properties
   * to Part 2 datastream data.
   *
   * @param id - The property resource identifier.
   * @param options - Optional query parameters for filtering datastreams.
   * @returns URL string for the property's datastreams endpoint.
   * @throws {EndpointError} If 'properties' is not available on this collection.
   *
   * @example
   * ```ts
   * const url = builder.getPropertyDataStreams('temperature-01');
   * // => "https://example.com/collections/iot/properties/temperature-01/datastreams"
   * ```
   *
   * @see https://docs.ogc.org/is/23-002/23-002.html#_datastream_resources
   */
  getPropertyDataStreams(id: string, options?: QueryOptions): string {
    this.assertResourceAvailable('properties');
    return this.buildResourceUrl('properties', id, 'datastreams', options);
  }

  /**
   * Returns the URL for listing control streams associated with a property.
   *
   * This is a Part 2 cross-reference endpoint linking Part 1 properties
   * to Part 2 control stream data.
   *
   * @param id - The property resource identifier.
   * @param options - Optional query parameters for filtering control streams.
   * @returns URL string for the property's control streams endpoint.
   * @throws {EndpointError} If 'properties' is not available on this collection.
   *
   * @example
   * ```ts
   * const url = builder.getPropertyControlStreams('valve-position-01');
   * // => "https://example.com/collections/iot/properties/valve-position-01/controlstreams"
   * ```
   *
   * @see https://docs.ogc.org/is/23-002/23-002.html#_control_stream_resources
   */
  getPropertyControlStreams(id: string, options?: QueryOptions): string {
    this.assertResourceAvailable('properties');
    return this.buildResourceUrl('properties', id, 'controlstreams', options);
  }

  /**
   * Returns the URL for retrieving a property's version history.
   *
   * @param id - The property resource identifier.
   * @param options - Optional query parameters for filtering history entries.
   * @returns URL string for the property history endpoint.
   * @throws {EndpointError} If 'properties' is not available on this collection.
   *
   * @example
   * ```ts
   * const url = builder.getPropertyHistory('temperature-01', { limit: 5 });
   * // => "https://example.com/collections/iot/properties/temperature-01/history?limit=5"
   * ```
   *
   * @see https://docs.ogc.org/is/23-001/23-001.html#_property_history
   */
  getPropertyHistory(id: string, options?: QueryOptions): string {
    this.assertResourceAvailable('properties');
    return this.buildResourceUrl('properties', id, 'history', options);
  }

  // ── DATASTREAMS ──

  /**
   * Returns the URL for querying all datastreams.
   *
   * DataStreams represent collections of observations from the same system
   * with shared schemas. Supports filtering by system, observed property,
   * and temporal parameters.
   *
   * @param options - Optional query parameters including `systemId`, `observedPropertyId`,
   *   `phenomenonTime`, `resultTime`, plus standard pagination and filtering.
   * @returns URL string for the datastreams collection endpoint.
   * @throws {EndpointError} If 'datastreams' is not available on this collection.
   *
   * @example
   * ```ts
   * const url = builder.getDataStreams({ limit: 10, observedPropertyId: 'temperature' });
   * // => "https://example.com/collections/iot/datastreams?limit=10&observedPropertyId=temperature"
   * ```
   *
   * @see https://docs.ogc.org/is/23-002/23-002.html#_datastream_resources
   */
  getDataStreams(options?: DatastreamQueryOptions): string {
    this.assertResourceAvailable('datastreams');
    return this.buildResourceUrl('datastreams', undefined, undefined, options);
  }

  /**
   * Returns the URL for retrieving a single datastream by ID.
   *
   * @param id - The datastream resource identifier.
   * @param options - Optional query parameters (e.g., format selection).
   * @returns URL string for the single datastream endpoint.
   * @throws {EndpointError} If 'datastreams' is not available on this collection.
   *
   * @example
   * ```ts
   * const url = builder.getDataStream('ds-001');
   * // => "https://example.com/collections/iot/datastreams/ds-001"
   * ```
   *
   * @see https://docs.ogc.org/is/23-002/23-002.html#_datastream_resources
   */
  getDataStream(id: string, options?: QueryOptions): string {
    this.assertResourceAvailable('datastreams');
    return this.buildResourceUrl('datastreams', id, undefined, options);
  }

  /**
   * Returns the URL for creating a new datastream.
   *
   * The request body (not part of the URL) must include the result schema,
   * observed properties, and system association.
   *
   * @returns URL string for the datastreams creation endpoint (POST).
   * @throws {EndpointError} If 'datastreams' is not available on this collection.
   *
   * @example
   * ```ts
   * const url = builder.createDataStream();
   * // => "https://example.com/collections/iot/datastreams"
   * ```
   *
   * @see https://docs.ogc.org/is/23-002/23-002.html#_datastream_resources
   */
  createDataStream(): string {
    this.assertResourceAvailable('datastreams');
    return this.buildResourceUrl('datastreams');
  }

  /**
   * Returns the URL for updating an existing datastream.
   *
   * Caution: schema changes may affect existing observations.
   *
   * @param id - The datastream resource identifier.
   * @returns URL string for the datastream update endpoint (PUT).
   * @throws {EndpointError} If 'datastreams' is not available on this collection.
   *
   * @example
   * ```ts
   * const url = builder.updateDataStream('ds-001');
   * // => "https://example.com/collections/iot/datastreams/ds-001"
   * ```
   *
   * @see https://docs.ogc.org/is/23-002/23-002.html#_datastream_resources
   */
  updateDataStream(id: string): string {
    this.assertResourceAvailable('datastreams');
    return this.buildResourceUrl('datastreams', id);
  }

  /**
   * Returns the URL for deleting a datastream.
   *
   * @param id - The datastream resource identifier.
   * @returns URL string for the datastream deletion endpoint (DELETE).
   * @throws {EndpointError} If 'datastreams' is not available on this collection.
   *
   * @example
   * ```ts
   * const url = builder.deleteDataStream('ds-001');
   * // => "https://example.com/collections/iot/datastreams/ds-001"
   * ```
   *
   * @see https://docs.ogc.org/is/23-002/23-002.html#_datastream_resources
   */
  deleteDataStream(id: string): string {
    this.assertResourceAvailable('datastreams');
    return this.buildResourceUrl('datastreams', id);
  }

  /**
   * Returns the URL for retrieving a datastream's result schema.
   *
   * The `obsFormat` query parameter is **required** per Part 2, Req 11.
   * Omitting it causes the server to return 400 Bad Request.
   *
   * @param id - The datastream resource identifier.
   * @param options - Optional query parameters. Should include `f` set to the
   *   desired observation format (e.g., `application/swe+json`).
   * @returns URL string for the datastream schema endpoint.
   * @throws {EndpointError} If 'datastreams' is not available on this collection.
   *
   * @example
   * ```ts
   * const url = builder.getDataStreamSchema('ds-001', { f: 'application/swe+json' });
   * // => "https://example.com/collections/iot/datastreams/ds-001/schema?f=application%2Fswe%2Bjson"
   * ```
   *
   * @see https://docs.ogc.org/is/23-002/23-002.html#req_datastream_schema
   */
  getDataStreamSchema(id: string, options?: QueryOptions): string {
    this.assertResourceAvailable('datastreams');
    return this.buildResourceUrl('datastreams', id, 'schema', options);
  }

  /**
   * Returns the URL for listing observations within a datastream.
   *
   * Supports temporal filtering via `phenomenonTime` and `resultTime`,
   * including the special `latest` value for `resultTime`.
   * Supports cursor-based pagination via the `cursor` parameter.
   *
   * @param id - The datastream resource identifier.
   * @param options - Optional query parameters including `phenomenonTime`,
   *   `resultTime`, `cursor`, plus standard pagination and filtering.
   * @returns URL string for the datastream's observations endpoint.
   * @throws {EndpointError} If 'datastreams' is not available on this collection.
   *
   * @example
   * ```ts
   * const url = builder.getDataStreamObservations('ds-001', { resultTime: 'latest', limit: 100 });
   * // => "https://example.com/collections/iot/datastreams/ds-001/observations?resultTime=latest&limit=100"
   * ```
   *
   * @see https://docs.ogc.org/is/23-002/23-002.html#_observation_resources
   */
  getDataStreamObservations(id: string, options?: ObservationQueryOptions): string {
    this.assertResourceAvailable('datastreams');
    return this.buildResourceUrl('datastreams', id, 'observations', options);
  }

  /**
   * Returns the URL for creating an observation within a datastream.
   *
   * The request body (not part of the URL) must conform to the datastream's
   * result schema.
   *
   * @param datastreamId - The datastream resource identifier.
   * @returns URL string for the observation creation endpoint (POST).
   * @throws {EndpointError} If 'datastreams' is not available on this collection.
   *
   * @example
   * ```ts
   * const url = builder.createObservation('ds-001');
   * // => "https://example.com/collections/iot/datastreams/ds-001/observations"
   * ```
   *
   * @see https://docs.ogc.org/is/23-002/23-002.html#_observation_resources
   */
  createObservation(datastreamId: string): string {
    this.assertResourceAvailable('datastreams');
    return this.buildResourceUrl('datastreams', datastreamId, 'observations');
  }

  /**
   * Returns the URL for listing systems that produce a datastream.
   *
   * @param id - The datastream resource identifier.
   * @param options - Optional query parameters for filtering systems.
   * @returns URL string for the datastream's systems endpoint.
   * @throws {EndpointError} If 'datastreams' is not available on this collection.
   *
   * @example
   * ```ts
   * const url = builder.getDataStreamSystems('ds-001');
   * // => "https://example.com/collections/iot/datastreams/ds-001/systems"
   * ```
   *
   * @see https://docs.ogc.org/is/23-002/23-002.html#_datastream_resources
   */
  getDataStreamSystems(id: string, options?: QueryOptions): string {
    this.assertResourceAvailable('datastreams');
    return this.buildResourceUrl('datastreams', id, 'systems', options);
  }

  /**
   * Returns the URL for listing procedures associated with a datastream.
   *
   * @param id - The datastream resource identifier.
   * @param options - Optional query parameters for filtering procedures.
   * @returns URL string for the datastream's procedures endpoint.
   * @throws {EndpointError} If 'datastreams' is not available on this collection.
   *
   * @example
   * ```ts
   * const url = builder.getDataStreamProcedures('ds-001');
   * // => "https://example.com/collections/iot/datastreams/ds-001/procedures"
   * ```
   *
   * @see https://docs.ogc.org/is/23-002/23-002.html#_datastream_resources
   */
  getDataStreamProcedures(id: string, options?: QueryOptions): string {
    this.assertResourceAvailable('datastreams');
    return this.buildResourceUrl('datastreams', id, 'procedures', options);
  }

  /**
   * Returns the URL for retrieving a datastream's version history.
   *
   * @param id - The datastream resource identifier.
   * @param options - Optional query parameters for filtering history entries.
   * @returns URL string for the datastream history endpoint.
   * @throws {EndpointError} If 'datastreams' is not available on this collection.
   *
   * @example
   * ```ts
   * const url = builder.getDataStreamHistory('ds-001', { limit: 5 });
   * // => "https://example.com/collections/iot/datastreams/ds-001/history?limit=5"
   * ```
   *
   * @see https://docs.ogc.org/is/23-002/23-002.html#_datastream_resources
   */
  getDataStreamHistory(id: string, options?: QueryOptions): string {
    this.assertResourceAvailable('datastreams');
    return this.buildResourceUrl('datastreams', id, 'history', options);
  }

  // ── OBSERVATIONS ──

  /**
   * Returns the URL for querying all observations.
   *
   * Observations represent actual measurement data from systems. Supports
   * temporal filtering via `phenomenonTime` and `resultTime` (including
   * the special `'latest'` value), plus cursor-based pagination for
   * efficient streaming of large time series.
   *
   * @param options - Optional query parameters including `phenomenonTime`,
   *   `resultTime`, plus standard pagination and filtering.
   * @returns URL string for the observations collection endpoint.
   * @throws {EndpointError} If 'observations' is not available on this collection.
   *
   * @example
   * ```ts
   * const url = builder.getObservations({ phenomenonTime: { start: new Date('2024-01-01') }, limit: 100 });
   * // => "https://example.com/collections/iot/observations?phenomenonTime=2024-01-01T00%3A00%3A00.000Z%2F..&limit=100"
   * ```
   *
   * @see https://docs.ogc.org/is/23-002/23-002.html#_observation_resources
   */
  getObservations(options?: ObservationQueryOptions): string {
    this.assertResourceAvailable('observations');
    return this.buildResourceUrl('observations', undefined, undefined, options);
  }

  /**
   * Returns the URL for retrieving a single observation by ID.
   *
   * @param id - The observation resource identifier.
   * @param options - Optional query parameters (e.g., format selection).
   * @returns URL string for the observation resource endpoint.
   * @throws {EndpointError} If 'observations' is not available on this collection.
   *
   * @example
   * ```ts
   * const url = builder.getObservation('obs-001');
   * // => "https://example.com/collections/iot/observations/obs-001"
   * ```
   *
   * @see https://docs.ogc.org/is/23-002/23-002.html#_observation_resources
   */
  getObservation(id: string, options?: QueryOptions): string {
    this.assertResourceAvailable('observations');
    return this.buildResourceUrl('observations', id, undefined, options);
  }

  /**
   * Returns the URL for updating an existing observation.
   *
   * @param id - The observation resource identifier.
   * @returns URL string for the observation update endpoint (PUT).
   * @throws {EndpointError} If 'observations' is not available on this collection.
   *
   * @example
   * ```ts
   * const url = builder.updateObservation('obs-001');
   * // => "https://example.com/collections/iot/observations/obs-001"
   * ```
   *
   * @see https://docs.ogc.org/is/23-002/23-002.html#_observation_resources
   */
  updateObservation(id: string): string {
    this.assertResourceAvailable('observations');
    return this.buildResourceUrl('observations', id);
  }

  /**
   * Returns the URL for deleting an observation.
   *
   * @param id - The observation resource identifier.
   * @returns URL string for the observation deletion endpoint (DELETE).
   * @throws {EndpointError} If 'observations' is not available on this collection.
   *
   * @example
   * ```ts
   * const url = builder.deleteObservation('obs-001');
   * // => "https://example.com/collections/iot/observations/obs-001"
   * ```
   *
   * @see https://docs.ogc.org/is/23-002/23-002.html#_observation_resources
   */
  deleteObservation(id: string): string {
    this.assertResourceAvailable('observations');
    return this.buildResourceUrl('observations', id);
  }

  /**
   * Returns the URL for retrieving the parent datastream of an observation.
   *
   * Each observation belongs to exactly one datastream, so this endpoint
   * returns a single resource (not a collection).
   *
   * @param id - The observation resource identifier.
   * @returns URL string for the observation's parent datastream endpoint.
   * @throws {EndpointError} If 'observations' is not available on this collection.
   *
   * @example
   * ```ts
   * const url = builder.getObservationDatastream('obs-001');
   * // => "https://example.com/collections/iot/observations/obs-001/datastream"
   * ```
   *
   * @see https://docs.ogc.org/is/23-002/23-002.html#_observation_resources
   */
  getObservationDatastream(id: string): string {
    this.assertResourceAvailable('observations');
    return this.buildResourceUrl('observations', id, 'datastream');
  }

  /**
   * Returns the URL for retrieving the sampling feature of an observation.
   *
   * Each observation targets at most one sampling feature, so this endpoint
   * returns a single resource (not a collection).
   *
   * @param id - The observation resource identifier.
   * @param options - Optional query parameters.
   * @returns URL string for the observation's sampling feature endpoint.
   * @throws {EndpointError} If 'observations' is not available on this collection.
   *
   * @example
   * ```ts
   * const url = builder.getObservationSamplingFeature('obs-001');
   * // => "https://example.com/collections/iot/observations/obs-001/samplingFeature"
   * ```
   *
   * @see https://docs.ogc.org/is/23-002/23-002.html#_observation_resources
   */
  getObservationSamplingFeature(id: string, options?: QueryOptions): string {
    this.assertResourceAvailable('observations');
    return this.buildResourceUrl('observations', id, 'samplingFeature', options);
  }

  /**
   * Returns the URL for retrieving the observing system of an observation.
   *
   * Each observation is produced by exactly one system, so this endpoint
   * returns a single resource (not a collection).
   *
   * @param id - The observation resource identifier.
   * @param options - Optional query parameters.
   * @returns URL string for the observation's observing system endpoint.
   * @throws {EndpointError} If 'observations' is not available on this collection.
   *
   * @example
   * ```ts
   * const url = builder.getObservationSystem('obs-001');
   * // => "https://example.com/collections/iot/observations/obs-001/system"
   * ```
   *
   * @see https://docs.ogc.org/is/23-002/23-002.html#_observation_resources
   */
  getObservationSystem(id: string, options?: QueryOptions): string {
    this.assertResourceAvailable('observations');
    return this.buildResourceUrl('observations', id, 'system', options);
  }

  /**
   * Returns the URL for retrieving an observation's version history.
   *
   * @param id - The observation resource identifier.
   * @param options - Optional query parameters for filtering history entries.
   * @returns URL string for the observation history endpoint.
   * @throws {EndpointError} If 'observations' is not available on this collection.
   *
   * @example
   * ```ts
   * const url = builder.getObservationHistory('obs-001', { limit: 5 });
   * // => "https://example.com/collections/iot/observations/obs-001/history?limit=5"
   * ```
   *
   * @see https://docs.ogc.org/is/23-002/23-002.html#_observation_resources
   */
  getObservationHistory(id: string, options?: QueryOptions): string {
    this.assertResourceAvailable('observations');
    return this.buildResourceUrl('observations', id, 'history', options);
  }

  // ── CONTROL STREAMS ──

  /**
   * Returns the URL for querying all control streams.
   *
   * ControlStreams represent command interfaces for controlling actuators
   * and systems. They mirror DataStreams architecturally but for
   * control/actuation rather than observation/sensing.
   *
   * @param options - Optional query parameters including `systemId`,
   *   `controlledPropertyId`, plus standard pagination and filtering.
   * @returns URL string for the control streams collection endpoint.
   * @throws {EndpointError} If 'controlStreams' is not available on this collection.
   *
   * @example
   * ```ts
   * const url = builder.getControlStreams({ limit: 10, systemId: 'sys-001' });
   * // => "https://example.com/collections/iot/controlstreams?limit=10&systemId=sys-001"
   * ```
   *
   * @see https://docs.ogc.org/is/23-002/23-002.html#_controlstream_resources
   */
  getControlStreams(options?: ControlStreamQueryOptions): string {
    this.assertResourceAvailable('controlStreams');
    return this.buildResourceUrl('controlStreams', undefined, undefined, options);
  }

  /**
   * Returns the URL for retrieving a single control stream by ID.
   *
   * @param id - The control stream resource identifier.
   * @param options - Optional query parameters (e.g., format selection).
   * @returns URL string for the single control stream endpoint.
   * @throws {EndpointError} If 'controlStreams' is not available on this collection.
   *
   * @example
   * ```ts
   * const url = builder.getControlStream('cs-001');
   * // => "https://example.com/collections/iot/controlstreams/cs-001"
   * ```
   *
   * @see https://docs.ogc.org/is/23-002/23-002.html#_controlstream_resources
   */
  getControlStream(id: string, options?: QueryOptions): string {
    this.assertResourceAvailable('controlStreams');
    return this.buildResourceUrl('controlStreams', id, undefined, options);
  }

  /**
   * Returns the URL for creating a new control stream.
   *
   * The request body (not part of the URL) must include the parameter schema,
   * controlled properties, and system association.
   *
   * @returns URL string for the control streams creation endpoint (POST).
   * @throws {EndpointError} If 'controlStreams' is not available on this collection.
   *
   * @example
   * ```ts
   * const url = builder.createControlStream();
   * // => "https://example.com/collections/iot/controlstreams"
   * ```
   *
   * @see https://docs.ogc.org/is/23-002/23-002.html#_controlstream_resources
   */
  createControlStream(): string {
    this.assertResourceAvailable('controlStreams');
    return this.buildResourceUrl('controlStreams');
  }

  /**
   * Returns the URL for updating an existing control stream.
   *
   * Caution: schema changes may affect pending commands.
   *
   * @param id - The control stream resource identifier.
   * @returns URL string for the control stream update endpoint (PUT).
   * @throws {EndpointError} If 'controlStreams' is not available on this collection.
   *
   * @example
   * ```ts
   * const url = builder.updateControlStream('cs-001');
   * // => "https://example.com/collections/iot/controlstreams/cs-001"
   * ```
   *
   * @see https://docs.ogc.org/is/23-002/23-002.html#_controlstream_resources
   */
  updateControlStream(id: string): string {
    this.assertResourceAvailable('controlStreams');
    return this.buildResourceUrl('controlStreams', id);
  }

  /**
   * Returns the URL for deleting a control stream.
   *
   * @param id - The control stream resource identifier.
   * @returns URL string for the control stream deletion endpoint (DELETE).
   * @throws {EndpointError} If 'controlStreams' is not available on this collection.
   *
   * @example
   * ```ts
   * const url = builder.deleteControlStream('cs-001');
   * // => "https://example.com/collections/iot/controlstreams/cs-001"
   * ```
   *
   * @see https://docs.ogc.org/is/23-002/23-002.html#_controlstream_resources
   */
  deleteControlStream(id: string): string {
    this.assertResourceAvailable('controlStreams');
    return this.buildResourceUrl('controlStreams', id);
  }

  /**
   * Returns the URL for retrieving a control stream's parameter schema.
   *
   * The `cmdFormat` query parameter is **required** per Part 2, Req 25.
   * Omitting it causes the server to return 400 Bad Request.
   * Pass it via the `f` option (e.g., `{ f: 'application/swe+json' }`).
   *
   * @param id - The control stream resource identifier.
   * @param options - Optional query parameters. Should include `f` set to the
   *   desired command format (e.g., `application/swe+json`).
   * @returns URL string for the control stream schema endpoint.
   * @throws {EndpointError} If 'controlStreams' is not available on this collection.
   *
   * @example
   * ```ts
   * const url = builder.getControlStreamSchema('cs-001', { f: 'application/swe+json' });
   * // => "https://example.com/collections/iot/controlstreams/cs-001/schema?f=application%2Fswe%2Bjson"
   * ```
   *
   * @see https://docs.ogc.org/is/23-002/23-002.html#req_controlstream_schema
   */
  getControlStreamSchema(id: string, options?: QueryOptions): string {
    this.assertResourceAvailable('controlStreams');
    return this.buildResourceUrl('controlStreams', id, 'schema', options);
  }

  /**
   * Returns the URL for listing commands within a control stream.
   *
   * Supports temporal filtering via `issueTime` and `executionTime`,
   * and cursor-based pagination via the `cursor` parameter.
   *
   * @param id - The control stream resource identifier.
   * @param options - Optional query parameters including `issueTime`,
   *   `executionTime`, `currentStatus`, plus standard pagination and filtering.
   * @returns URL string for the control stream's commands endpoint.
   * @throws {EndpointError} If 'controlStreams' is not available on this collection.
   *
   * @example
   * ```ts
   * const url = builder.getControlStreamCommands('cs-001', { limit: 50 });
   * // => "https://example.com/collections/iot/controlstreams/cs-001/commands?limit=50"
   * ```
   *
   * @see https://docs.ogc.org/is/23-002/23-002.html#_command_resources
   */
  getControlStreamCommands(id: string, options?: CommandQueryOptions): string {
    this.assertResourceAvailable('controlStreams');
    return this.buildResourceUrl('controlStreams', id, 'commands', options);
  }

  /**
   * Returns the URL for checking command feasibility on a control stream.
   *
   * Feasibility checking allows testing whether a command can be executed
   * before actually submitting it. The request body (not part of the URL)
   * must contain the command parameters to validate.
   *
   * @param controlStreamId - The control stream resource identifier.
   * @returns URL string for the feasibility checking endpoint (POST).
   * @throws {EndpointError} If 'controlStreams' is not available on this collection.
   *
   * @example
   * ```ts
   * const url = builder.checkCommandFeasibility('cs-001');
   * // => "https://example.com/collections/iot/controlstreams/cs-001/feasibility"
   * ```
   *
   * @see https://docs.ogc.org/is/23-002/23-002.html#_controlstream_resources
   */
  checkCommandFeasibility(controlStreamId: string): string {
    this.assertResourceAvailable('controlStreams');
    return this.buildResourceUrl('controlStreams', controlStreamId, 'feasibility');
  }

  // ── COMMANDS ──

  /**
   * Returns the URL for querying all commands.
   *
   * Commands represent tasking requests sent to systems for actuation via
   * control streams. They are the control equivalent of Observations —
   * instructions that flow to systems rather than data that flows from them.
   *
   * @param options - Optional query parameters including `issueTime`,
   *   `executionTime`, `currentStatus`, plus standard pagination and filtering.
   * @returns URL string for the commands collection endpoint.
   * @throws {EndpointError} If 'commands' is not available on this collection.
   *
   * @example
   * ```ts
   * const url = builder.getCommands({ issueTime: { start: new Date('2024-01-01') }, limit: 100 });
   * // => "https://example.com/collections/iot/commands?issueTime=2024-01-01T00%3A00%3A00.000Z%2F..&limit=100"
   * ```
   *
   * @see https://docs.ogc.org/is/23-002/23-002.html#_command_resources
   */
  getCommands(options?: CommandQueryOptions): string {
    this.assertResourceAvailable('commands');
    return this.buildResourceUrl('commands', undefined, undefined, options);
  }

  /**
   * Returns the URL for retrieving a single command by ID.
   *
   * @param id - The command resource identifier.
   * @param options - Optional query parameters (e.g., format selection).
   * @returns URL string for the single command endpoint.
   * @throws {EndpointError} If 'commands' is not available on this collection.
   *
   * @example
   * ```ts
   * const url = builder.getCommand('cmd-001');
   * // => "https://example.com/collections/iot/commands/cmd-001"
   * ```
   *
   * @see https://docs.ogc.org/is/23-002/23-002.html#_command_resources
   */
  getCommand(id: string, options?: QueryOptions): string {
    this.assertResourceAvailable('commands');
    return this.buildResourceUrl('commands', id, undefined, options);
  }

  /**
   * Returns the URL for creating a single command within a control stream.
   *
   * The request body (not part of the URL) must conform to the control stream's
   * parameter schema.
   *
   * @param controlStreamId - The control stream resource identifier.
   * @returns URL string for the command creation endpoint (POST).
   * @throws {EndpointError} If 'controlStreams' is not available on this collection.
   *
   * @example
   * ```ts
   * const url = builder.createCommand('cs-001');
   * // => "https://example.com/collections/iot/controlStreams/cs-001/commands"
   * ```
   *
   * @see https://docs.ogc.org/is/23-002/23-002.html#_command_resources
   */
  createCommand(controlStreamId: string): string {
    this.assertResourceAvailable('controlStreams');
    return this.buildResourceUrl('controlStreams', controlStreamId, 'commands');
  }

  /**
   * Returns the URL for bulk-creating commands within a control stream.
   *
   * The request body (not part of the URL) must contain an array of command
   * objects, each conforming to the control stream's parameter schema.
   *
   * @param controlStreamId - The control stream resource identifier.
   * @returns URL string for the bulk command creation endpoint (POST).
   * @throws {EndpointError} If 'controlStreams' is not available on this collection.
   *
   * @example
   * ```ts
   * const url = builder.createCommands('cs-001');
   * // => "https://example.com/collections/iot/controlStreams/cs-001/commands"
   * ```
   *
   * @see https://docs.ogc.org/is/23-002/23-002.html#_command_resources
   */
  createCommands(controlStreamId: string): string {
    this.assertResourceAvailable('controlStreams');
    return this.buildResourceUrl('controlStreams', controlStreamId, 'commands');
  }

  /**
   * Returns the URL for updating an existing command.
   *
   * @param id - The command resource identifier.
   * @returns URL string for the command update endpoint (PUT).
   * @throws {EndpointError} If 'commands' is not available on this collection.
   *
   * @example
   * ```ts
   * const url = builder.updateCommand('cmd-001');
   * // => "https://example.com/collections/iot/commands/cmd-001"
   * ```
   *
   * @see https://docs.ogc.org/is/23-002/23-002.html#_command_resources
   */
  updateCommand(id: string): string {
    this.assertResourceAvailable('commands');
    return this.buildResourceUrl('commands', id);
  }

  /**
   * Returns the URL for deleting a command.
   *
   * @param id - The command resource identifier.
   * @returns URL string for the command deletion endpoint (DELETE).
   * @throws {EndpointError} If 'commands' is not available on this collection.
   *
   * @example
   * ```ts
   * const url = builder.deleteCommand('cmd-001');
   * // => "https://example.com/collections/iot/commands/cmd-001"
   * ```
   *
   * @see https://docs.ogc.org/is/23-002/23-002.html#_command_resources
   */
  deleteCommand(id: string): string {
    this.assertResourceAvailable('commands');
    return this.buildResourceUrl('commands', id);
  }

  /**
   * Returns the URL for retrieving the status of a command.
   *
   * Command status tracks lifecycle state transitions: PENDING → ACCEPTED →
   * EXECUTING → COMPLETED/FAILED/CANCELED.
   *
   * @param id - The command resource identifier.
   * @returns URL string for the command status endpoint.
   * @throws {EndpointError} If 'commands' is not available on this collection.
   *
   * @example
   * ```ts
   * const url = builder.getCommandStatus('cmd-001');
   * // => "https://example.com/collections/iot/commands/cmd-001/status"
   * ```
   *
   * @see https://docs.ogc.org/is/23-002/23-002.html#_command_resources
   */
  getCommandStatus(id: string): string {
    this.assertResourceAvailable('commands');
    return this.buildResourceUrl('commands', id, 'status');
  }

  /**
   * Returns the URL for updating the status of a command.
   *
   * Used for system-generated status updates as a command progresses
   * through its lifecycle (e.g., from PENDING to EXECUTING).
   *
   * @param id - The command resource identifier.
   * @returns URL string for the command status update endpoint (PATCH).
   * @throws {EndpointError} If 'commands' is not available on this collection.
   *
   * @example
   * ```ts
   * const url = builder.updateCommandStatus('cmd-001');
   * // => "https://example.com/collections/iot/commands/cmd-001/status"
   * ```
   *
   * @see https://docs.ogc.org/is/23-002/23-002.html#_command_resources
   */
  updateCommandStatus(id: string): string {
    this.assertResourceAvailable('commands');
    return this.buildResourceUrl('commands', id, 'status');
  }

  /**
   * Returns the URL for retrieving the result of a command.
   *
   * Command results contain execution output conforming to the control
   * stream's result schema.
   *
   * @param id - The command resource identifier.
   * @returns URL string for the command result endpoint.
   * @throws {EndpointError} If 'commands' is not available on this collection.
   *
   * @example
   * ```ts
   * const url = builder.getCommandResult('cmd-001');
   * // => "https://example.com/collections/iot/commands/cmd-001/result"
   * ```
   *
   * @see https://docs.ogc.org/is/23-002/23-002.html#_command_resources
   */
  getCommandResult(id: string): string {
    this.assertResourceAvailable('commands');
    return this.buildResourceUrl('commands', id, 'result');
  }

  /**
   * Returns the URL for cancelling a command.
   *
   * Cancellation requests the system to abort a pending or executing command.
   * The actual cancellation may be asynchronous — poll the command status
   * to confirm transition to CANCELED.
   *
   * @param id - The command resource identifier.
   * @returns URL string for the command cancellation endpoint (POST).
   * @throws {EndpointError} If 'commands' is not available on this collection.
   *
   * @example
   * ```ts
   * const url = builder.cancelCommand('cmd-001');
   * // => "https://example.com/collections/iot/commands/cmd-001/cancel"
   * ```
   *
   * @see https://docs.ogc.org/is/23-002/23-002.html#_command_resources
   */
  cancelCommand(id: string): string {
    this.assertResourceAvailable('commands');
    return this.buildResourceUrl('commands', id, 'cancel');
  }
}
