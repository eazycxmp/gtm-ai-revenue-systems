# GTM AI Revenue Systems

Spec-first, composable GTM automation built with **Model Context Protocol (MCP)**.  
This hub documents the servers I’m building for a full outbound → enrichment → CRM → comms pipeline.

> Goal: keep contracts (inputs/outputs) for every step visible, testable, and reusable across hosts (Claude Desktop, agents, CI).

---

## Architecture (high level)

Host (Claude Desktop)
│
▼
[mcp-server-scraper] ──► targets (JSON)
│
▼
[mcp-server-enrichment] ──► enriched contacts (JSON)
│
▼
[mcp-server-hubspot] ──► CRM upserts / deals / activities
│
▼
[mcp-server-comms] ──► email / SMS sequences (dry-run → live)
│
▼
[mcp-server-playbook] ──► subject lines, openers, call flows

perl
Copy code

Each server exposes 1–3 tools with explicit **JSON I/O** and runnable examples in `examples/`.

---

Why not just n8n workflows?

You could wire up Gmail → HubSpot → Slack in a drag-and-drop tool like n8n. That’s fine for quick hacks — but brittle, opaque, and unshareable.

This system is different:

Spec-first. Every server exposes strict JSON I/O contracts that can be tested, versioned, and reused.

Composable. Each step (scraper, enrichment, CRM, comms) is a separate server — plug them together in any order or swap providers without breaking the pipeline.

Portable. Works across Claude Desktop, CI/CD, or future AI agents. You’re not locked to one UI.

## Repos

| Server | Purpose | Key Tools | Repo |
|---|---|---|---|
| Scraper | Find targets by query/region | `scrape_targets`, `dedupe` | https://github.com/eazycxmp/mcp-server-scraper |
| Enrichment | Enrich & verify (Apollo/Clay/n8n) | `enrich_contact`, `verify_email`, `batch_enrich_via_n8n` | https://github.com/eazycxmp/mcp-server-enrichment |
| HubSpot | CRM upserts & deals | `upsert_contact`, `create_deal`, `log_activity` | https://github.com/eazycxmp/mcp-server-hubspot |
| Comms | Email/SMS orchestration | `send_email`, `send_sms`, `pause_resume_sequence` | https://github.com/eazycxmp/mcp-server-comms |
| Playbook | Copy & call flows | `subject_line_generator`, `call_openers` | https://github.com/eazycxmp/mcp-server-playbook |

> Each repo includes: `README.md` with Input/Output snippets, `examples/` with runnable JSON, `tools/`, and a `server.py` runner.

---

## Quickstart (local)

Clone the servers side-by-side:

```bash
cd ~
git clone https://github.com/eazycxmp/mcp-server-scraper.git
git clone https://github.com/eazycxmp/mcp-server-enrichment.git
git clone https://github.com/eazycxmp/mcp-server-hubspot.git
git clone https://github.com/eazycxmp/mcp-server-comms.git
git clone https://github.com/eazycxmp/mcp-server-playbook.git
Test one server (scraper):

bash
Copy code
cd ~/mcp-server-scraper
python server.py scrape_targets @examples/sample_input.json
python server.py dedupe @examples/sample_dedupe_input.json