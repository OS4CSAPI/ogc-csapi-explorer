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
const SI_UNKNOWN = '1'              // Unknown (yellow diamond frame)
const SI_FRIEND = '3'
const SI_NEUTRAL = '4'
const SI_HOSTILE = '6'
const STATUS_PRESENT = '0'
const HQ_NONE = '0'
const ECHELON_NONE = '00'
const ECHELON_TEAM = '11'
const MOD_NONE = '0000'

// Symbol Sets
const SS_AIR = '01'
const SS_SPACE = '05'
const SS_LAND_UNIT = '10'
const SS_LAND_EQUIPMENT = '15'
const SS_LAND_INSTALLATION = '20'
const SS_SEA_SURFACE = '30'
const SS_ACTIVITY = '40'
const SS_METOC = '45'              // Meteorological / Oceanographic
const SS_SIGINT = '52'

// Entity codes (6 digits) — Land Equipment (SS 15)
const ENT_SENSOR = '220100'           // Generic sensor
const ENT_SENSOR_EMPLACED = '220200'  // Sensor, emplaced
const ENT_RADAR = '220300'            // Radar
const ENT_GENERATOR = '200700'        // Generator set
const ENT_VEHICLE = '140100'          // Armored vehicle

// Entity codes — Air (SS 01)
const ENT_UAV = '110700'              // UAV / Drone
const ENT_FIXED_WING = '110100'       // Fixed-wing aircraft
const ENT_ROTARY = '110200'           // Rotary wing

// Entity codes — Space (SS 05)
const ENT_SATELLITE = '110100'        // Military satellite (generic)
const ENT_SPACE_STATION = '120900'    // Civilian space station
const MOD1_LEO = '01'                 // Modifier 1: Low Earth Orbit

// Entity codes — Land Unit (SS 10)
const ENT_UNIT_GENERIC = '110000'     // Generic unit
const ENT_UNIT_INFANTRY = '121100'    // Infantry
const ENT_UNIT_RECON = '110500'       // Reconnaissance
const ENT_UNIT_SIGNAL = '111700'      // Signal / comms
const ENT_UNIT_ENGINEER = '111300'    // Engineer

// Entity codes — Land Installation (SS 20)
const ENT_INSTALLATION = '110000'     // Generic installation
const ENT_OBSERVATION_POST = '111200' // Observation post / monitoring station
const ENT_RETRANS_SITE = '112700'     // Retransmission site

// Entity codes — Land Unit Intelligence branch (SS 10, 15xxxx)
const ENT_MI = '151000'               // Military Intelligence (MI dagger icon)
const ENT_SIGNAL_RADIO_RELAY = '111002' // Signal – Radio Relay (full frame)

// Entity codes — SIGINT Ground (SS 52)
const ENT_SIGINT_COMMS = '110100'     // SIGINT Communications (antenna icon)
const ENT_SIGINT_RADAR = '110300'     // SIGINT Radar (dish + signal lines)

// Entity codes — Activity (SS 40)
const ENT_ACTIVITY = '110000'         // Generic activity/event

// Entity codes — Sea Surface (SS 30)
const ENT_SEA_SURFACE = '110000'      // Generic sea surface

// Entity codes — METOC (SS 45)
const ENT_WEATHER_BUOY = '121104'     // Weather Buoy — Surface
const ENT_WEATHER_SENSOR = '111101'   // Stationary Weather Sensor — Land

// ─── SIDC Builder ──────────────────────────────────────────────────────────────

function buildSIDC(
  identity: string,
  symbolSet: string,
  entity: string,
  status = STATUS_PRESENT,
  modifiers = MOD_NONE,
  echelon = ECHELON_NONE,
): string {
  return `${VERSION}${CONTEXT_REALITY}${identity}${symbolSet}${status}${HQ_NONE}${echelon}${entity}${modifiers}`
}

// ─── Keyword Matching ──────────────────────────────────────────────────────────

type KeywordRule = {
  keywords: string[]
  identity: string
  symbolSet: string
  entity: string
  echelon?: string
  /** Override modifier digits (pos 17-20), default '0000' */
  modifiers?: string
  /** Override: use a legacy letter SIDC verbatim (milsymbol supports both formats) */
  letterSidc?: string
}

/**
 * Keyword rules for classifying systems. Order matters — first match wins.
 * More specific rules go first.
 */
const SYSTEM_RULES: KeywordRule[] = [
  // ISS / space station → Neutral satellite (green SV frame), LEO modifier
  { keywords: ['iss', 'space station', 'zarya'],
    identity: SI_NEUTRAL, symbolSet: SS_SPACE, entity: ENT_SATELLITE,
    modifiers: `${MOD1_LEO}00` },
  // Other satellite / orbital tracker → Friend military satellite
  { keywords: ['satellite', 'orbital', 'sgp4', 'norad'],
    identity: SI_FRIEND, symbolSet: SS_SPACE, entity: ENT_SATELLITE },
  // Relay / retransmission device → Signal Radio Relay (Land Unit full frame)
  { keywords: ['relay', 'retrans', 'repeater', 'retransmission'],
    identity: SI_FRIEND, symbolSet: SS_LAND_UNIT, entity: ENT_SIGNAL_RADIO_RELAY },
  // Environment Agency Hydrology Station → Friend Sensor Emplaced
  // River level, river flow, rainfall, and groundwater stations are closest to USGS Water/CO-OPS gauges.
  { keywords: ['environment agency', 'ea hydrology', 'hydrology', 'river level', 'river flow', 'rainfall', 'groundwater'],
    identity: SI_FRIEND, symbolSet: SS_LAND_EQUIPMENT, entity: ENT_SENSOR_EMPLACED,
    letterSidc: 'SFGPEWRH-------' },
  // UK-AIR air-quality monitoring stations → Friend Sensor Emplaced
  // Fixed public-health/environmental monitoring sites are closest to the established station sensor family.
  { keywords: ['uk-air', 'uk air', 'air quality', 'air pollution', 'pollutant', 'no2', 'pm10', 'pm2.5', 'ozone'],
    identity: SI_FRIEND, symbolSet: SS_LAND_EQUIPMENT, entity: ENT_SENSOR_EMPLACED,
    letterSidc: 'SFGPEWRH-------' },
  // Met Office Weather DataHub land observations -> Friend Sensor Emplaced
  { keywords: ['met office', 'weather datahub', 'land observations', 'weather observation', 'weather station'],
    identity: SI_FRIEND, symbolSet: SS_LAND_EQUIPMENT, entity: ENT_SENSOR_EMPLACED,
    letterSidc: 'SFGPEWRH-------' },
  // BGS SensorThings / UKGEOS groundwater telemetry -> Friend Sensor Emplaced
  { keywords: ['bgs', 'british geological survey', 'sensorthings', 'ukgeos', 'geothermal', 'hydro logger'],
    identity: SI_FRIEND, symbolSet: SS_LAND_EQUIPMENT, entity: ENT_SENSOR_EMPLACED,
    letterSidc: 'SFGPEWRH-------' },
  // Monitoring site / intel collector → MI + Sensor (letter SIDC for correct icon rendering)
  { keywords: ['monitoring site', 'mon-site', 'observation post', 'monitoring node', 'monitoring station'],
    identity: SI_FRIEND, symbolSet: SS_LAND_UNIT, entity: ENT_MI,
    letterSidc: 'SFGPUUMRS------' },
  // Sensor Employment Team → MI unit (MI dagger in Land Unit rectangle, team echelon)
  { keywords: ['sensor employment', 'set-', 'set team', 'infantry team', 'set-a', 'set-b'],
    identity: SI_FRIEND, symbolSet: SS_LAND_UNIT, entity: ENT_MI, echelon: ECHELON_TEAM },
  // Acoustic / microphone sensor (C-UAS specific)
  { keywords: ['acoustic', 'microphone', 'odas', 'mic array', 'sound', 'audio', 'sensor array'],
    identity: SI_FRIEND, symbolSet: SS_LAND_EQUIPMENT, entity: ENT_SENSOR_EMPLACED,
    letterSidc: 'SFGPEWRH-------' },
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
  // Fixed wing aircraft / ADS-B feed
  { keywords: ['aircraft', 'airplane', 'fixed-wing', 'plane', 'opensky', 'ads-b', 'adsb'],
    identity: SI_FRIEND, symbolSet: SS_AIR, entity: ENT_FIXED_WING },
  // Weather / METOC / meteorological sensor → EW Radar/Sensor (letter SIDC)
  // Doctrinal SIDC: 10034500001111010000 (METOC SS unsupported by milsymbol)
  // Renders: blue Friend circle + antenna + measurement lines
  { keywords: ['weather', 'metoc', 'meteorolog', 'asos', 'nws', 'metar', 'awx', 'aviation weather'],
    identity: SI_FRIEND, symbolSet: SS_LAND_EQUIPMENT, entity: ENT_SENSOR_EMPLACED,
    letterSidc: 'SFGPEWRH-------' },
  // Radar / lidar → keep as land equipment
  { keywords: ['radar', 'lidar'],
    identity: SI_NEUTRAL, symbolSet: SS_LAND_EQUIPMENT, entity: ENT_RADAR },
  // Camera / EO / video imagery → supported emplaced sensor symbol.
  // The previous laser entity renders as an empty equipment frame in milsymbol 3.x.
  { keywords: ['webcam', 'weathercam', 'traffic camera', 'camera', 'cctv', 'video', 'electro-optical', 'eo ', 'imagery', 'image reference', 'poster image', 'photo', 'optical'],
    identity: SI_FRIEND, symbolSet: SS_LAND_EQUIPMENT, entity: ENT_SENSOR_EMPLACED,
    letterSidc: 'SFGPEWRH-------' },
  // Vehicle-based sensor
  { keywords: ['vehicle', 'car', 'truck', 'mobile platform'],
    identity: SI_FRIEND, symbolSet: SS_LAND_EQUIPMENT, entity: ENT_VEHICLE },
  // Communications / signal
  { keywords: ['comm', 'radio', 'signal', 'antenna', 'telemetry', 'transmit'],
    identity: SI_FRIEND, symbolSet: SS_LAND_UNIT, entity: ENT_UNIT_SIGNAL },
  // Reconnaissance / surveillance
  { keywords: ['recon', 'surveillance', 'monitor'],
    identity: SI_FRIEND, symbolSet: SS_LAND_UNIT, entity: ENT_UNIT_RECON },
  // NDBC Weather Buoy → Friend Sensor Emplaced (blue circle + sensor star + wavy line)
  // NOAA is a national org → Friend (blue), not Neutral (green)
  // Doctrinal SIDC: 10034500001211040000 (METOC SS unsupported by milsymbol)
  { keywords: ['buoy', 'ndbc'],
    identity: SI_FRIEND, symbolSet: SS_LAND_EQUIPMENT, entity: ENT_SENSOR_EMPLACED,
    letterSidc: 'SFGPEWRH-------' },
  // CO-OPS Tide Gauge Station → Friend Sensor Emplaced (same family as NDBC/NWS)
  // NOAA CO-OPS coastal water level stations, fixed pier/platform installations
  { keywords: ['co-ops', 'coops', 'tide', 'water level', 'coastal obs'],
    identity: SI_FRIEND, symbolSet: SS_LAND_EQUIPMENT, entity: ENT_SENSOR_EMPLACED,
    letterSidc: 'SFGPEWRH-------' },
  // USGS Water Monitoring Station → Friend Sensor Emplaced
  // USGS stream gauges measuring discharge / gage height — same sensor family as NDBC/CO-OPS
  { keywords: ['usgs', 'nwis', 'streamflow', 'stream gauge', 'gage height', 'discharge'],
    identity: SI_FRIEND, symbolSet: SS_LAND_EQUIPMENT, entity: ENT_SENSOR_EMPLACED,
    letterSidc: 'SFGPEWRH-------' },
  // Sea / marine / vessel (generic)
  { keywords: ['marine', 'ocean', 'sea', 'ship', 'vessel', 'boat'],
    identity: SI_NEUTRAL, symbolSet: SS_SEA_SURFACE, entity: ENT_SEA_SURFACE },
  // SIGINT
  { keywords: ['sigint', 'signal intelligence', 'intercept'],
    identity: SI_FRIEND, symbolSet: SS_SIGINT, entity: '110100' },
]

function matchKeywords(text: string, rules: KeywordRule[]): KeywordRule | null {
  const lower = text.toLowerCase()
  for (const rule of rules) {
    if (rule.keywords.some(kw => {
      // Short keywords (≤3 chars after trim) use word-boundary regex to prevent
      // false substring matches (e.g. 'iss' matching inside 'retransmission').
      const trimmed = kw.trim()
      if (trimmed.length <= 3) {
        return new RegExp(`\\b${trimmed}\\b`).test(lower)
      }
      return lower.includes(kw)
    })) {
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

  const props = rawData?.properties || rawData || {}
  const name = props.name || rawData?.name || rawData?.label || ''
  const description = props.description || rawData?.description || ''
  const featureType = props.featureType || rawData?.featureType || ''
  const platformTitle = props['platform@link']?.title || ''
  const uid = props.uid || rawData?.uid || ''
  const searchText = `${name} ${description} ${featureType} ${platformTitle} ${uid}`

  let sidc: string

  switch (resourceType) {
    case 'deployments': {
      // Deployments get keyword-based STANAG classification
      const rule = matchKeywords(searchText, SYSTEM_RULES)
      if (rule) {
        sidc = rule.letterSidc
          ? rule.letterSidc
          : buildSIDC(rule.identity, rule.symbolSet, rule.entity, STATUS_PRESENT, rule.modifiers || MOD_NONE, rule.echelon)
      } else {
        // Default deployment → friendly land unit
        sidc = buildSIDC(SI_FRIEND, SS_LAND_UNIT, ENT_UNIT_GENERIC)
      }
      break
    }
    case 'systems': {
      // Systems → friendly ground sensor (generic, but milsymbols not rendered for systems)
      sidc = buildSIDC(SI_FRIEND, SS_LAND_EQUIPMENT, ENT_SENSOR)
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
      // Datastreams inherit parent system classification if possible,
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
  const pixelSize = symbolSize === 'tiny' ? 16 : symbolSize === 'small' ? 22 : 26

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

// ─── SENREP Target-Type Symbol Rendering ───────────────────────────────────────

/**
 * Map from SENREP tgtTyp values to SIDC codes.
 * Uses "Unknown" standard identity (yellow diamond frame for Air).
 */
const SENREP_TGT_SIDC: Record<string, string> = {
  UAS:    buildSIDC(SI_UNKNOWN, SS_AIR, ENT_UAV),
  // Future: add more target type mappings here
  // VEHICL: buildSIDC(SI_UNKNOWN, SS_LAND_EQUIPMENT, ENT_VEHICLE),
  // PERS:   buildSIDC(SI_UNKNOWN, SS_LAND_UNIT, ENT_UNIT_INFANTRY),
}

/**
 * Render a NATO STANAG symbol for a SENREP observation based on its target type.
 * Returns null if no symbol mapping exists for the given tgtTyp.
 *
 * @param tgtTyp  The SENREP target type (e.g. 'UAS', 'VEHICL', 'PERS', 'UNKN')
 * @param size    Pixel size for the rendered symbol (default 32)
 * @returns       { svgDataUrl, anchor, size, sidc } or null
 */
export function renderSenrepSymbol(
  tgtTyp: string,
  size = 32,
): MilSymbolResult | null {
  const sidc = SENREP_TGT_SIDC[tgtTyp?.toUpperCase()]
  if (!sidc) return null

  const cacheKey = `senrep-${sidc}-${size}`
  const cached = symbolCache.get(cacheKey)
  if (cached) return cached

  try {
    const sym = new ms.Symbol(sidc, { size })
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
    console.warn('[symbol-mapper] Failed to render SENREP symbol for tgtTyp', tgtTyp, e)
    return null
  }
}

/**
 * Clear the symbol render cache (e.g., on theme change).
 */
export function clearSymbolCache(): void {
  symbolCache.clear()
}
