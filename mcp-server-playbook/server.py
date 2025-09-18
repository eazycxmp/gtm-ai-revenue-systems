#!/usr/bin/env python3
# server.py
import json, sys
from tools.scrape_targets import scrape_targets
from tools.dedupe import dedupe

HELP = """\
Usage:
  python server.py scrape_targets '{"query":"rugby clubs","region":"Southeast USA"}'
  python server.py dedupe @examples/sample_dedupe_input.json
"""

def main():
    if len(sys.argv) < 2:
        sys.stderr.write(HELP + "\n"); sys.exit(1)

    tool = sys.argv[1]

    # Support: pass JSON inline OR @path/to/file.json
    args = {}
    if len(sys.argv) >= 3:
        arg = sys.argv[2]
        if arg.startswith("@"):
            path = arg[1:]
            with open(path, "r") as f:
                payload = json.load(f)
        else:
            payload = json.loads(arg)
        args = payload

    if tool == "scrape_targets":
        out = scrape_targets(query=args.get("query",""), region=args.get("region",""))
    elif tool == "dedupe":
        records = args.get("records", [])
        out = dedupe(records)
    else:
        sys.stderr.write(f"Unknown tool: {tool}\n{HELP}\n"); sys.exit(2)

    print(json.dumps(out, indent=2))

if __name__ == "__main__":
    main()


