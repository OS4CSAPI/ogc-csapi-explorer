/**
 * Error thrown when an endpoint operation cannot be completed.
 *
 * Used across all OGC API modules (Connected Systems, Features, STAC, etc.)
 * for resource availability errors, HTTP errors, and cross-origin issues.
 *
 * This class is intentionally isolated in its own module (no XML or other
 * heavy dependencies) so that lightweight consumers — such as CSAPI-only
 * users who never touch WMS/WFS — do not pull in the XML parsing stack
 * via transitive imports.
 *
 * @see ServiceExceptionError in `./errors.ts` for OWS XML error parsing
 */
export class EndpointError extends Error {
  constructor(
    message: string,
    public readonly httpStatus?: number,
    public readonly isCrossOriginRelated?: boolean
  ) {
    super(message);
    this.name = 'EndpointError';
  }
}
