/**
 * Stub for @rgrove/parse-xml.
 *
 * The library's shared/xml-utils.ts imports this package, but the demo
 * only uses the CSAPI adapter (JSON-only) so the XML parser is never
 * actually called at runtime.  This empty stub satisfies the bundler.
 */
export function parseXml() {
  throw new Error('@rgrove/parse-xml is not available in this build')
}
export class XmlDocument {}
export class XmlElement {}
export class XmlText {}
export class XmlComment {}
export class XmlCdata {}
export class XmlProcessingInstruction {}
