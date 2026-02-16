import { reactive } from 'vue'

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
}

export const connection = reactive<ServerConnection>({
  connected: false,
  label: '',
  baseUrl: '',
  authHeaders: {},
  landingPage: null,
  conformance: [],
  collections: [],
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
