
# Vortex Rugby Union -> Team -> Contact scraper
# Usage:
#   python vortex_union_scraper.py --start_url "https://example-union.org" --max_pages 400 --out "union_contacts.csv"
#
# What it does:
# - Crawls the union domain for "Teams", "Clubs", "Members" pages
# - Extracts outbound links that look like team websites or Linktree/socials
# - For each team, discovers a likely Contact/About/Board page and scrapes emails and likely roles
# - Writes a tidy CSV compatible with your demand-gen template
#
# Notes:
# - Be respectful: add delays, obey robots.txt if required, and don't hammer sites.
# - This is a heuristic scraper; expect some misses. You can re-run with different keywords.

import argparse
import csv
import re
import time
from urllib.parse import urljoin, urlparse
from collections import deque

import requests
from bs4 import BeautifulSoup

EMAIL_RE = re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}")
ROLE_HINTS = [
    "president", "vp", "vice president", "secretary", "treasurer",
    "captain", "coach", "director", "board", "committee", "officer"
]
TEAM_PAGE_HINTS = [
    "team", "teams", "clubs", "members", "our-clubs", "club-directory", "find-a-club"
]
CONTACT_PAGE_HINTS = [
    "contact", "about", "board", "committee", "officers", "leadership", "staff"
]

HEADERS = {
    "User-Agent": "VortexScraper/1.0 (+https://vortex-rugby.example)"
}

def get_soup(url, timeout=15):
    try:
        r = requests.get(url, headers=HEADERS, timeout=timeout)
        if r.status_code == 200 and "text/html" in r.headers.get("Content-Type", ""):
            return BeautifulSoup(r.text, "html.parser")
    except Exception:
        return None
    return None

def clean_url(base, link):
    href = link.get("href")
    if not href:
        return None
    href = urljoin(base, href)
    if href.startswith("mailto:") or href.startswith("javascript:"):
        return None
    p = urlparse(href)
    if not p.scheme.startswith("http"):
        return None
    return href

def text_contains_any(text, hints):
    t = (text or "").lower()
    return any(h in t for h in hints)

def guess_team_links(union_url, max_pages=400, crawl_delay=0.8):
    visited = set()
    queue = deque([union_url])
    same_domain = urlparse(union_url).netloc
    external_team_links = set()

    while queue and len(visited) < max_pages:
        url = queue.popleft()
        if url in visited:
            continue
        visited.add(url)

        soup = get_soup(url)
        if not soup:
            continue

        page_text = soup.get_text(" ", strip=True).lower()
        strong_hint_page = text_contains_any(url.lower(), TEAM_PAGE_HINTS) or text_contains_any(page_text, TEAM_PAGE_HINTS)

        for a in soup.find_all("a"):
            href = clean_url(url, a)
            if not href:
                continue

            if urlparse(href).netloc == same_domain:
                if href not in visited and (len(visited) + len(queue) < max_pages):
                    queue.append(href)
            else:
                anchor_txt = (a.get_text() or "").strip().lower()
                if strong_hint_page or "club" in anchor_txt or "rugby" in anchor_txt or "rfc" in anchor_txt:
                    external_team_links.add(href)

        time.sleep(crawl_delay)

    return list(external_team_links)

def find_contact_like_pages(base_url):
    soup = get_soup(base_url)
    if not soup:
        return []

    candidates = set()
    for a in soup.find_all("a"):
        href = clean_url(base_url, a)
        if not href:
            continue
        anchor = (a.get_text() or "").lower()
        if text_contains_any(href.lower(), CONTACT_PAGE_HINTS) or text_contains_any(anchor, CONTACT_PAGE_HINTS):
            candidates.add(href)

    if not candidates:
        candidates.add(base_url)
    return list(candidates)

def extract_emails_and_roles(url):
    soup = get_soup(url)
    if not soup:
        return []

    text = soup.get_text("\n", strip=True)
    emails = set(EMAIL_RE.findall(text))
    results = []

    if not emails:
        return results

    lines = text.splitlines()
    for i, line in enumerate(lines):
        found = EMAIL_RE.findall(line)
        if not found:
            continue
        context = " ".join(lines[max(0, i-2): i+3]).lower()
        role_guess = ""
        for hint in ROLE_HINTS:
            if hint in context:
                role_guess = hint
                break
        for e in found:
            results.append((e, role_guess))
    return results

def normalize_team_name(url):
    host = urlparse(url).netloc
    pretty = host.replace("www.", "").replace(".org", "").replace(".com", "").replace(".net", "")
    pretty = pretty.replace("-", " ").replace("_", " ").title()
    return pretty

def main():
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("--start_url", required=True, help="Union root website URL")
    ap.add_argument("--max_pages", type=int, default=400, help="Max pages to crawl on union site")
    ap.add_argument("--out", default="union_contacts.csv", help="Output CSV path")
    ap.add_argument("--delay", type=float, default=0.8, help="Delay between requests (seconds)")
    args = ap.parse_args()

    union_url = args.start_url
    print(f"[INFO] Crawling union site: {union_url}")
    team_links = guess_team_links(union_url, max_pages=args.max_pages, crawl_delay=args.delay)
    print(f"[INFO] Found {len(team_links)} potential team links.")

    fieldnames = [
        "Union Name","Union Website","Team Name","Team Website","Contact Page URL",
        "City/State/Region","Level (College/Men/Women/HS)","Sevens or XVs",
        "Primary Contact Name","Primary Contact Role","Primary Contact Email",
        "Secondary Contact Name","Secondary Contact Role","Secondary Contact Email",
        "All Emails Found (comma-separated)","Season Window","Tournaments (Noted)",
        "Notes (source snippets/URLs)","Lifecycle Stage","Status","Owner",
        "Sequence/Playbook","Last Touch (ISO)","Next Step (Due Date)","Priority (H/M/L)",
        "LinkedIn (Team)","LinkedIn (Primary Contact)","Instagram","Facebook",
        "Acquisition Channel","Campaign","UTM_Source","UTM_Medium","UTM_Campaign"
    ]

    rows_written = 0
    with open(args.out, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fieldnames)
        w.writeheader()

        for team_url in team_links:
            team_name = normalize_team_name(team_url)
            contact_pages = find_contact_like_pages(team_url)

            all_emails = set()
            primary_email = ""
            primary_role = ""
            secondary_email = ""
            secondary_role = ""

            for cp in contact_pages:
                pairs = extract_emails_and_roles(cp)
                for e, role in pairs:
                    all_emails.add(e)
                    if not primary_email:
                        primary_email = e
                        primary_role = role or ""
                    elif not secondary_email and e != primary_email:
                        secondary_email = e
                        secondary_role = role or ""

                time.sleep(args.delay)

            row = {
                "Union Name": "",
                "Union Website": union_url,
                "Team Name": team_name,
                "Team Website": team_url,
                "Contact Page URL": ";".join(contact_pages) if contact_pages else "",
                "City/State/Region": "",
                "Level (College/Men/Women/HS)": "",
                "Sevens or XVs": "",
                "Primary Contact Name": "",
                "Primary Contact Role": primary_role,
                "Primary Contact Email": primary_email,
                "Secondary Contact Name": "",
                "Secondary Contact Role": secondary_role,
                "Secondary Contact Email": secondary_email,
                "All Emails Found (comma-separated)": ",".join(sorted(all_emails)),
                "Season Window": "",
                "Tournaments (Noted)": "",
                "Notes (source snippets/URLs)": "",
                "Lifecycle Stage": "New Lead",
                "Status": "New",
                "Owner": "",
                "Sequence/Playbook": "Club Kit - Intro",
                "Last Touch (ISO)": "",
                "Next Step (Due Date)": "",
                "Priority (H/M/L)": "M",
                "LinkedIn (Team)": "",
                "LinkedIn (Primary Contact)": "",
                "Instagram": "",
                "Facebook": "",
                "Acquisition Channel": "Scraped",
                "Campaign": "Union Crawl",
                "UTM_Source": "union",
                "UTM_Medium": "crawler",
                "UTM_Campaign": "union_to_teams"
            }
            w.writerow(row)
            rows_written += 1

    print(f"[DONE] Wrote {rows_written} rows to {args.out}")

if __name__ == "__main__":
    main()
