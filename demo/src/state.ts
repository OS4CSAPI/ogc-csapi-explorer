import { reactive } from 'vue'

/**
 * A dynamic warning detected during the connection handshake.
 * These are NOT hardcoded per-server — they're detected at connect time
 * based on what the server actually returns (or fails to return).
 */
export interface ConnectionWarning {
  severity: 'warn' | 'info' | 'success'
  summary: string
  detail: string
}

/**
 * Shared application state — connection info accessible to all components
 */
export interface ServerConnection {
  connected: boolean
  label: string
  baseUrl: string
  authHeaders: Record<string, string>
  landingPage: any | null
  conformance: string[]
  collections: any[]
  warnings: ConnectionWarning[]
}

export const connection = reactive<ServerConnection>({
  connected: false,
  label: '',
  baseUrl: '',
  authHeaders: {},
  landingPage: null,
  conformance: [],
  collections: [],
  warnings: [],
})

/**
 * The 9 CSAPI resource types with metadata for the UI
 */
export interface ResourceTypeInfo {
  key: string
  label: string
  plural: string
  icon: string
  part: 1 | 2
  readOnly: boolean
  /** For resource types whose create is nested (observations → datastream, commands → controlStream) */
  createParentType?: string
  createParentLabel?: string
}

export const RESOURCE_TYPES: ResourceTypeInfo[] = [
  { key: 'systems', label: 'System', plural: 'Systems', icon: 'pi pi-server', part: 1, readOnly: false },
  { key: 'deployments', label: 'Deployment', plural: 'Deployments', icon: 'pi pi-map', part: 1, readOnly: false },
  { key: 'procedures', label: 'Procedure', plural: 'Procedures', icon: 'pi pi-cog', part: 1, readOnly: false },
  { key: 'samplingFeatures', label: 'Sampling Feature', plural: 'Sampling Features', icon: 'pi pi-map-marker', part: 1, readOnly: false },
  { key: 'properties', label: 'Property', plural: 'Properties', icon: 'pi pi-tags', part: 1, readOnly: true },
  { key: 'datastreams', label: 'Datastream', plural: 'Datastreams', icon: 'pi pi-chart-line', part: 2, readOnly: false },
  { key: 'observations', label: 'Observation', plural: 'Observations', icon: 'pi pi-eye', part: 2, readOnly: false, createParentType: 'datastreams', createParentLabel: 'Datastream ID' },
  { key: 'controlStreams', label: 'Control Stream', plural: 'Control Streams', icon: 'pi pi-sliders-h', part: 2, readOnly: false },
  { key: 'commands', label: 'Command', plural: 'Commands', icon: 'pi pi-send', part: 2, readOnly: false, createParentType: 'controlStreams', createParentLabel: 'Control Stream ID' },
]

export function getResourceType(key: string): ResourceTypeInfo | undefined {
  return RESOURCE_TYPES.find((r) => r.key === key)
}

/**
 * Defines the nested/related resource navigation available from each parent resource type.
 * Each entry maps a parent type to the list of child relations the CSAPI spec supports.
 */
export interface RelatedResourceLink {
  /** Resource type key of the child collection (e.g., 'systems' for subsystems) */
  childType: string
  /** Button label (e.g., 'Subsystems') */
  label: string
  /** PrimeIcons class */
  icon: string
  /** The nested endpoint segment (e.g., 'subsystems', 'datastreams') */
  relation: string
}

export const RELATED_RESOURCES: Record<string, RelatedResourceLink[]> = {
  systems: [
    { childType: 'systems', label: 'Subsystems', icon: 'pi pi-sitemap', relation: 'subsystems' },
    { childType: 'datastreams', label: 'Datastreams', icon: 'pi pi-chart-line', relation: 'datastreams' },
    { childType: 'controlStreams', label: 'Control Streams', icon: 'pi pi-sliders-h', relation: 'controlstreams' },
    { childType: 'samplingFeatures', label: 'Sampling Features', icon: 'pi pi-map-marker', relation: 'samplingFeatures' },
    { childType: 'deployments', label: 'Deployments', icon: 'pi pi-map', relation: 'deployments' },
    { childType: 'procedures', label: 'Procedures', icon: 'pi pi-cog', relation: 'procedures' },
  ],
  deployments: [
    { childType: 'deployments', label: 'Subdeployments', icon: 'pi pi-sitemap', relation: 'subdeployments' },
    { childType: 'systems', label: 'Deployed Systems', icon: 'pi pi-server', relation: 'systems' },
  ],
  datastreams: [
    { childType: 'observations', label: 'Observations', icon: 'pi pi-eye', relation: 'observations' },
    { childType: 'systems', label: 'Observing Systems', icon: 'pi pi-server', relation: 'systems' },
    { childType: 'procedures', label: 'Procedures', icon: 'pi pi-cog', relation: 'procedures' },
  ],
  controlStreams: [
    { childType: 'commands', label: 'Commands', icon: 'pi pi-send', relation: 'commands' },
  ],
  procedures: [
    { childType: 'systems', label: 'Implementing Systems', icon: 'pi pi-server', relation: 'systems' },
    { childType: 'datastreams', label: 'Datastreams', icon: 'pi pi-chart-line', relation: 'datastreams' },
  ],
  samplingFeatures: [
    { childType: 'systems', label: 'Sampling Systems', icon: 'pi pi-server', relation: 'systems' },
    { childType: 'observations', label: 'Observations', icon: 'pi pi-eye', relation: 'observations' },
  ],
  properties: [
    { childType: 'systems', label: 'Systems', icon: 'pi pi-server', relation: 'systems' },
    { childType: 'datastreams', label: 'Datastreams', icon: 'pi pi-chart-line', relation: 'datastreams' },
    { childType: 'controlStreams', label: 'Control Streams', icon: 'pi pi-sliders-h', relation: 'controlstreams' },
  ],
}
