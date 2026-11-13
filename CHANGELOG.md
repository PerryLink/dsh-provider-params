# Changelog

## [0.2.0] — 2026-11-13

### Breaking

- **Tool names no longer contain a dot.** The four tools are now `params_map`,
  `params_compare`, `params_vendors` and `json_repair`. Providers validate
  `tools[].name` against `^[a-zA-Z0-9_-]+$`; the old dotted spelling
  invalidated the whole `tools` array, so the plugin registered but every
  request carrying its tools was rejected with `Invalid 'tools[N].name'`.
  Minor bump because tool names are part of the 0.1.0 compatibility promise —
  update prompts, saved calls and permission rules that still use the old
  dotted spelling.
- `test/tool-name-wire.test.mjs` pins the wire pattern, so a new tool cannot
  reintroduce a dot, drop the `params_` / `json_` namespace or duplicate an
  existing name.
- READMEs, `TROUBLESHOOTING.md`, the quickstart runner, the generated SVG
  diagrams and the quickstart hero banners all use the underscore spelling, so
  a repository-wide search no longer finds dotted tool names.

## [0.1.0] — 2026-11-03

### Stable

- First non-alpha release: tool names and the parameter table are covered by a
  compatibility promise (breaking changes require a minor bump).
- Four read-only tools: `params_map` maps a request fragment between 11 LLM
  vendors and reports mapped / dropped / added / adjusted / unknown;
  `params_compare` returns a 13-row semantic diff; `params_vendors` lists the
  11 × 13 field table; `json_repair` repairs broken JSON deterministically
  without inventing business values.
- Ships a five-language README, a quickstart sample with checked-in goldens, a
  real screenshot and generated hero/diagram artwork.

## 0.1.0-alpha.1 — 2026-11-02

- First public alpha of `dsh-provider-params`.
- Static 11-vendor × 13-canonical-field table, ported from the documented
  vendor wire shapes; no network, no model call, no filesystem writes.
- Bounded, deterministic JSON repair with a fixed strategy order and a
  fail-closed error code per failure mode.
- Local only: no network, no model call, no upload.
