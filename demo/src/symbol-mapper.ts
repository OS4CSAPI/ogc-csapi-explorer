/**
 * MIL-STD-2525D symbol mapper for CSAPI resources.
 *
 * Maps CSAPI resource types (systems, deployments, datastreams, etc.)
 * to NATO military symbol SIDC codes, then renders them as SVG icons
 * using the milsymbol library for display on OpenLayers maps.
 *
 * SIDC structure (20-digit, MIL-STD-2525D):
 *   Pos 1-2:  Version (10 = 2525D)
 *   Pos 3:    Context (0 = Reality)
 *   Pos 4:    Standard Identity (3 = Friend, 4 = Neutral, 6 = Hostile)
 *   Pos 5-6:  Symbol Set (01=Air, 10=LandUnit, 15=LandEquipment, 20=Installation, 40=Activity)
 *   Pos 7:    Status (0 = Present, 1 = Planned/Anticipated)
 *   Pos 8:    HQ/TF/Dummy (0 = none)
 *   Pos 9-10: Echelon/Mobility (00 = none)
 *   Pos 11-16: Entity code (6 digits — the actual icon)
 *   Pos 17-18: Modifier 1
 *   Pos 19-20: Modifier 2
 */

import ms from 'milsymbol'

// ─── SIDC Building Blocks ──────────────────────────────────────────────────────

const VERSION = '10'                // MIL-STD-2525D
const CONTEXT_REALITY = '0'
const SI_FRIEND = '3'
const SI_NEUTRAL = '4'
const STATUS_PRESENT = '0'
const HQ_NONE = '0'
const ECHELON_NONE = '00'
const MOD_NONE = '0000'

// Symbol Sets
const SS_AIR = '01'
const SS_LAND_UNIT = '10'
const SS_LAND_EQUIPMENT = '15'
const SS_LAND_INSTALLATION = '20'
const SS_SEA_SURFACE = '30'
const SS_ACTIVITY = '40'
const SS_SIGINT = '52'

// Entity codes (6 digits) — Land Equipment (SS 15)
const ENT_SENSOR = '220100'           // Generic sensor
const ENT_SENSOR_EMPLACED = '220200'  // Sensor, emplaced
const ENT_RADAR = '220300'            // Radar
const ENT_GENERATOR = '200700'        // Generator set
const ENT_LASER = '201000'            // Laser
const ENT_VEHICLE = '140100'          // Armored vehicle

// Entity codes — Air (SS 01)
const ENT_UAV = '110700'              // UAV / Drone
const ENT_FIXED_WING = '110100'       // Fixed-wing aircraft
const ENT_ROTARY = '110200'           // Rotary wing

// Entity codes — Land Unit (SS 10)
const ENT_UNIT_GENERIC = '110000'     // Generic unit
const ENT_UNIT_RECON = '110500'       // Reconnaissance
const ENT_UNIT_SIGNAL = '111700'      // Signal / comms
const ENT_UNIT_ENGINEER = '111300'    // Engineer

// Entity codes — Land Installation (SS 20)
const ENT_INSTALLATION = '110000'     // Generic installation

// Entity codes — Activity (SS 40)
const ENT_ACTIVITY = '110000'         // Generic activity/event

// Entity codes — Sea Surface (SS 30)
const ENT_SEA_SURFACE = '110000'      // Generic sea surface

// ─── SIDC Builder ──────────────────────────────────────────────────────────────

function buildSIDC(
  identity: string,
  symbolSet: string,
  entity: string,
  status = STATUS_PRESENT,
  modifiers = MOD_NONE,
): string {
  return `${VERSION}${CONTEXT_REALITY}${identity}${symbolSet}${status}${HQ_NONE}${ECHELON_NONE}${entity}${modifiers}`
}

// ─── Keyword Matching ──────────────────────────────────────────────────────────

type KeywordRule = {
  keywords: string[]
  identity: string
  symbolSet: string
  entity: string
}

/**
 * Keyword rules for classifying systems. Order matters — first match wins.
 * More specific rules go first.
 */
const SYSTEM_RULES: KeywordRule[] = [
  // Acoustic / microphone sensor (C-UAS specific)
  { keywords: ['acoustic', 'microphone', 'odas', 'mic array', 'sound', 'audio', 'sensor array'],
    identity: SI_FRIEND, symbolSet: SS_LAND_EQUIPMENT, entity: ENT_SENSOR_EMPLACED },
  // String processor / processing node
  { keywords: ['processor', 'triangulat', 'string proc', 'strproc', 'processing'],
    identity: SI_FRIEND, symbolSet: SS_LAND_EQUIPMENT, entity: ENT_SENSOR },
  // Monitoring / observation team
  { keywords: ['monitoring', 'mon-team', 'observer', 'senrep'],
    identity: SI_FRIEND, symbolSet: SS_LAND_UNIT, entity: ENT_UNIT_RECON },
  // UAV/drone
  { keywords: ['drone', 'uav', 'unmanned', 'uas', 'quadcopter', 'cubepilot', 'fcu'],
    identity: SI_FRIEND, symbolSet: SS_AIR, entity: ENT_UAV },
  // Rotary wing aircraft
  { keywords: ['helicopter', 'rotor', 'rotary'],
    identity: SI_FRIEND, symbolSet: SS_AIR, entity: ENT_ROTARY },
  // Fixed wing aircraft
  { keywords: ['aircraft', 'airplane', 'fixed-wing', 'plane'],
    identity: SI_FRIEND, symbolSet: SS_AIR, entity: ENT_FIXED_WING },
  // Weather / METOC / radar
  { keywords: ['weather', 'metoc', 'meteorolog', 'radar', 'lidar'],
    identity: SI_NEUTRAL, symbolSet: SS_LAND_EQUIPMENT, entity: ENT_RADAR },
  // Camera / EO / video
  { keywords: ['camera', 'video', 'electro-optical', 'eo ', 'imagery', 'photo', 'optical'],
    identity: SI_FRIEND, symbolSet: SS_LAND_EQUIPMENT, entity: ENT_LASER },
  // Vehicle-based sensor
  { keywords: ['vehicle', 'car', 'truck', 'mobile platform'],
    identity: SI_FRIEND, symbolSet: SS_LAND_EQUIPMENT, entity: ENT_VEHICLE },
  // Communications / signal
  { keywords: ['comm', 'radio', 'signal', 'antenna', 'telemetry', 'transmit'],
    identity: SI_FRIEND, symbolSet: SS_LAND_UNIT, entity: ENT_UNIT_SIGNAL },
  // Reconnaissance / surveillance
  { keywords: ['recon', 'surveillance', 'monitor'],
    identity: SI_FRIEND, symbolSet: SS_LAND_UNIT, entity: ENT_UNIT_RECON },
  // Sea / marine / buoy
  { keywords: ['buoy', 'marine', 'ocean', 'sea', 'ship', 'vessel', 'boat'],
    identity: SI_NEUTRAL, symbolSet: SS_SEA_SURFACE, entity: ENT_SEA_SURFACE },
  // SIGINT
  { keywords: ['sigint', 'signal intelligence', 'intercept'],
    identity: SI_FRIEND, symbolSet: SS_SIGINT, entity: '110100' },
]

function matchKeywords(text: string, rules: KeywordRule[]): KeywordRule | null {
  const lower = text.toLowerCase()
  for (const rule of rules) {
    if (rule.keywords.some(kw => lower.includes(kw))) {
      return rule
    }
  }
  return null
}

// ─── Public API ────────────────────────────────────────────────────────────────

export type SymbolSize = 'normal' | 'small' | 'tiny'

export interface MilSymbolResult {
  sidc: string
  svgDataUrl: string
  anchor: { x: number; y: number }
  size: { width: number; height: number }
}

// Cache rendered symbols to avoid re-generating SVGs
const symbolCache = new Map<string, MilSymbolResult>()

/**
 * Classify a CSAPI resource and return a rendered MIL-STD-2525 symbol.
 */
export function getSymbolForResource(
  resourceType: string,
  rawData: any,
  symbolSize: SymbolSize = 'normal',
): MilSymbolResult | null {
  // Observation tracks and points don't get milsymbols (they use line/dot styles)
  if (resourceType === 'observationTracks' || resourceType === 'observationPoints') {
    return null
  }

  const name = rawData?.properties?.name || rawData?.name || rawData?.label || ''
  const description = rawData?.properties?.description || rawData?.description || ''
  const featureType = rawData?.properties?.featureType || rawData?.featureType || ''
  const searchText = `${name} ${description} ${featureType}`

  let sidc: string

  switch (resourceType) {
    case 'systems': {
      const rule = matchKeywords(searchText, SYSTEM_RULES)
      if (rule) {
        sidc = buildSIDC(rule.identity, rule.symbolSet, rule.entity)
      } else {
        // Default system → friendly ground sensor
        sidc = buildSIDC(SI_FRIEND, SS_LAND_EQUIPMENT, ENT_SENSOR)
      }
      break
    }
    case 'deployments': {
      // Deployments → land unit rectangle (friendly)
      sidc = buildSIDC(SI_FRIEND, SS_LAND_UNIT, ENT_UNIT_GENERIC)
      break
    }
    case 'procedures': {
      // Procedures → neutral ground installation
      sidc = buildSIDC(SI_NEUTRAL, SS_LAND_INSTALLATION, ENT_INSTALLATION)
      break
    }
    case 'samplingFeatures': {
      // Sampling features → emplaced sensor (neutral)
      sidc = buildSIDC(SI_NEUTRAL, SS_LAND_EQUIPMENT, ENT_SENSOR_EMPLACED)
      break
    }
    case 'datastreams': {
      // DataStreams inherit parent system classification if possible,
      // but default to a friendly sensor with smaller rendering
      const dsName = rawData?.name || rawData?.outputName || ''
      const rule = matchKeywords(`${dsName} ${searchText}`, SYSTEM_RULES)
      if (rule) {
        sidc = buildSIDC(rule.identity, rule.symbolSet, rule.entity)
      } else {
        sidc = buildSIDC(SI_FRIEND, SS_LAND_EQUIPMENT, ENT_SENSOR)
      }
      break
    }
    case 'controlStreams': {
      // Control streams → friendly land unit with signal modifier
      sidc = buildSIDC(SI_FRIEND, SS_LAND_UNIT, ENT_UNIT_SIGNAL)
      break
    }
    default:
      sidc = buildSIDC(SI_NEUTRAL, SS_LAND_EQUIPMENT, ENT_SENSOR)
  }

  // Determine pixel size
  const pixelSize = symbolSize === 'tiny' ? 20 : symbolSize === 'small' ? 28 : 38

  // Check cache
  const cacheKey = `${sidc}-${pixelSize}`
  const cached = symbolCache.get(cacheKey)
  if (cached) return cached

  // Render via milsymbol
  try {
    const sym = new ms.Symbol(sidc, {
      size: pixelSize,
    })

    const svgString = sym.asSVG()
    const svgDataUrl = 'data:image/svg+xml;charset=utf-8,' + encodeURIComponent(svgString)
    const anchor = sym.getAnchor()
    const symbolSize2 = sym.getSize()

    const result: MilSymbolResult = {
      sidc,
      svgDataUrl,
      anchor: { x: anchor.x, y: anchor.y },
      size: { width: symbolSize2.width, height: symbolSize2.height },
    }

    symbolCache.set(cacheKey, result)
    return result
  } catch (e) {
    console.warn('[symbol-mapper] Failed to render SIDC', sidc, e)
    return null
  }
}

/**
 * Determine the appropriate symbol size for a resource type.
 */
export function getSymbolSizeForType(resourceType: string): SymbolSize {
  if (resourceType === 'datastreams' || resourceType === 'controlStreams') return 'small'
  return 'normal'
}

/**
 * Clear the symbol render cache (e.g., on theme change).
 */
export function clearSymbolCache(): void {
  symbolCache.clear()
}
