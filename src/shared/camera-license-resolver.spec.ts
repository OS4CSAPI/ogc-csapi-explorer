import { rankCameraProcedureCandidates } from '../../demo/src/composables/camera-license-resolver.js'

describe('camera license procedure ranking', () => {
  it('prefers the digitraffic weathercam procedure when source hints match', () => {
    const ranked = rankCameraProcedureCandidates(
      'Digitraffic Weather Camera Image',
      'Digitraffic Weather Camera Image',
      'https://tie.digitraffic.fi/api/weathercam/v1/stations/C01507/data',
      [
        {
          id: '04gg',
          properties: {
            uid: 'urn:os4csapi:procedure:digitraffic-road-weather:v1',
            name: 'Digitraffic Road Weather Observation v1',
            description: 'Publishes road-weather station observations.',
          },
        },
        {
          id: '04k0',
          properties: {
            uid: 'urn:os4csapi:procedure:digitraffic-weathercam:v1',
            name: 'Digitraffic Weather Camera Image v1',
            description: 'Publishes image-reference observations for weather camera presets.',
          },
        },
        {
          id: '04ag',
          properties: {
            uid: 'urn:os4csapi:procedure:ndbc:buoycam-imagery:v1',
            name: 'NDBC BuoyCAM Imagery v1',
            description: 'Publishes NDBC buoy camera images.',
          },
        },
      ],
    )

    expect(ranked[0]?.id).toBe('04k0')
    expect(ranked[0]?.score).toBeGreaterThan(ranked[1]?.score ?? -1)
  })
})
