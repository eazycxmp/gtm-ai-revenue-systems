# MCP Server — Enrichment

This server exposes two GTM-friendly tools the model (or you) can call:

- `scrape_targets(query, region)` → returns a list of orgs with basic fields (stubbed today; swap in real scraper later)
- `dedupe(records)` → removes duplicates by `(name,email)` pair

> Why this repo exists: show a **spec-first** pattern for exposing data-gathering tools the same way every time, so an AI host (e.g., Claude Desktop) can orchestrate scrape → enrich → CRM → comms.

## Tools (I/O)

### `scrape_targets`
**Input**
```json
{ "query": "rugby clubs", "region": "Southeast USA" }
```

**Output (truncated)**
```json
[
  {
    "name": "Charlotte Rugby Club",
    "email": "info@charlotterugby.com",
    "url": "https://charlotterugby.com",
    "region": "Southeast USA",
    "query": "rugby clubs"
  }
]
```
---

### `dedupe`

**Input**
```json
{
  "records": [
    { "name": "X", "email": "x@x.com" },
    { "name": "X", "email": "x@x.com" }
  ]
}
```   

**Output**
```json
[
  { "name": "X", "email": "x@x.com" }
]
```   



