export interface ProcedureCandidateLike {
  id?: string
  uid?: string
  name?: string
  description?: string
  properties?: {
    uid?: string
    name?: string
    description?: string
  }
}

export interface RankedProcedureCandidate {
  id: string
  score: number
}

export function rankCameraProcedureCandidates(
  cameraName: string,
  productLabel: string,
  sourceHintText: string,
  procedureItems: ProcedureCandidateLike[],
): RankedProcedureCandidate[] {
  const sourceHint = sourceHintText.toLowerCase()
  const nameTokens = cameraName
    .toLowerCase()
    .split(/[^a-z0-9]+/)
    .filter(token => token.length >= 4 && !['live', 'image', 'camera'].includes(token))
  const outputHint = productLabel.toLowerCase()

  return procedureItems
    .map(item => {
      const props = item?.properties || item || {}
      const hay = `${props.uid || ''} ${props.name || ''} ${props.description || ''}`.toLowerCase()
      let score = 0
      if (/weathercam|weather\s+camera|camera/.test(hay)) score += 2
      if (outputHint && hay.includes(outputHint)) score += 2
      for (const token of nameTokens) {
        if (hay.includes(token)) score += 1
      }
      if (sourceHint.includes('digitraffic') && hay.includes('digitraffic')) score += 4
      if (sourceHint.includes('fintraffic') && hay.includes('fintraffic')) score += 4
      return { id: item?.id || '', score }
    })
    .filter(item => item.id && item.score > 0)
    .sort((a, b) => b.score - a.score)
    .slice(0, 8)
}
