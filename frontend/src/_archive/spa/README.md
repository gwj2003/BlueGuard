# Archived SPA Sources

This directory contains the previous Vue SPA implementation that is not used by the current multi-page legacy entry flow.

## Why archived

- Active entrypoints are:
  - `/src/entries/index.js`
  - `/src/entries/privacy-policy.js`
  - `/src/entries/terms-conditions.js`
- The archived files were not imported by these entrypoints.

## Restore if needed

Move selected files back under `src/` and reconnect them via active HTML entry files and `vite.config.js`.
