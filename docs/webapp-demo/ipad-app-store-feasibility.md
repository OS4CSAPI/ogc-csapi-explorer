# iPad App Store Feasibility Assessment

**Date:** 2026-02-21  
**Status:** Feasibility study — no implementation started

## Summary

The CSAPI Explorer demo webapp (Vue 3 + PrimeVue + Vite) can be packaged as a native iPad app and submitted to the Apple App Store. The most viable path is **Capacitor**, which wraps the existing codebase in a native iOS WebView shell with minimal code changes.

## Distribution Options

### Option 1: Capacitor (Recommended)

[Capacitor](https://capacitorjs.com/) by Ionic wraps the existing Vue 3 app in a native WebView with minimal changes. The entire codebase stays as-is; an iOS shell is added around it.

- **Effort:** Low — `npm install @capacitor/core @capacitor/ios`, `npx cap add ios`, build, open in Xcode
- **Result:** The exact webapp running as a native iOS app with access to native APIs if needed
- **App Store acceptance:** Well-established — many production apps use this approach
- **Consideration:** Apple has occasionally scrutinized "thin wrapper" apps, but CSAPI Explorer has genuine utility (server diagnostics, data model visualization, map views, CRUD operations, automated smoke testing) which makes it a substantive engineering tool, not a bookmark

### Option 2: Progressive Web App (PWA)

Add a service worker and web manifest to make the app installable on iPad home screens without going through the App Store.

- **Effort:** Very low — Vite has a PWA plugin (`vite-plugin-pwa`)
- **Limitation:** No App Store presence; slightly fewer native capabilities
- **Benefit:** No Apple review process; no $99/year developer account

### Option 3: Tauri v2 (Emerging)

[Tauri v2](https://v2.tauri.app/) supports iOS targets using the system WebView (no bundled engine). Lighter footprint than Capacitor, but iOS support is newer and less battle-tested.

## Engineering Considerations

| Concern | Current State | Required Work |
|---------|--------------|---------------|
| **CORS / Proxy** | Dev server uses Vite proxy routes (`/api/osh`, `/api/52north`) to bypass CORS | Native app has no dev proxy. Options: (a) lightweight cloud relay service, (b) configure target servers to send CORS headers, (c) use Capacitor's native HTTP plugin which bypasses CORS |
| **Apple Developer Account** | Not set up | $99/year enrollment required for App Store distribution |
| **App Review** | N/A | Apple reviews for functionality, privacy policy, metadata. The app would likely pass — it's a legitimate developer/engineering tool with clear utility |
| **OpenLayers Map** | Works in desktop browsers | Works fine in mobile Safari WebView — well-tested on iOS |
| **Responsive Layout** | Designed for desktop-width screens | Would need CSS/layout adjustments for iPad viewport and touch interactions |
| **PrimeVue Components** | Desktop-optimized | PrimeVue has mobile-friendly defaults but some panels/tables may need touch-friendly sizing |

## CORS Solution Detail

The biggest technical hurdle is the CORS proxy. Three approaches:

1. **Capacitor HTTP Plugin** — `@capacitor/http` makes native HTTP requests that bypass browser CORS restrictions entirely. This is the cleanest solution and requires changing `fetch()` calls to use the Capacitor HTTP API (or a thin adapter layer).

2. **Cloud Relay** — Deploy a lightweight proxy (e.g., Cloudflare Worker, small Express server) that forwards requests to CSAPI servers. Adds latency and a hosting dependency.

3. **Server-side CORS headers** — Requires cooperation from CSAPI server operators to add `Access-Control-Allow-Origin` headers. Not feasible for third-party servers.

**Recommendation:** Option 1 (Capacitor HTTP plugin) is the most self-contained and does not require external infrastructure or server cooperation.

## Recommendation

Start with **Capacitor** for the App Store path. The only significant engineering work is solving the CORS proxy problem via the Capacitor HTTP plugin. The rest of the app (Vue 3 components, OpenLayers map, PrimeVue UI, router) would work as-is inside the native WebView. A PWA version could be added in parallel with near-zero effort as a fallback for users who prefer browser-based access.

## Estimated Effort

| Task | Effort |
|------|--------|
| Capacitor scaffold + iOS project setup | ~1 hour |
| CORS adapter layer (Capacitor HTTP plugin) | ~4–8 hours |
| Responsive/touch layout adjustments | ~4–8 hours |
| Apple Developer enrollment + provisioning | ~1–2 hours |
| App Store metadata, screenshots, privacy policy | ~2–4 hours |
| Testing on physical iPad | ~2–4 hours |
| **Total** | **~14–27 hours** |
