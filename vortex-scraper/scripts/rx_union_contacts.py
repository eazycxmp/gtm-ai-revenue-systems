import argparse, csv, re, time
from urllib.parse import urljoin
import requests
from bs4 import BeautifulSoup

BASE = "https://xplorer.rugby"
HEADERS = {"User-Agent": "VortexScraper-RX/1.0 (+https://vortex-rugby.example)"}
EMAIL_RE = re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}")

def get_soup(url, timeout=20):
    try:
        r = requests.get(url, headers=HEADERS, timeout=timeout)
        if r.status_code == 200 and "text/html" in r.headers.get("Content-Type",""):
            return BeautifulSoup(r.text, "html.parser")
    except Exception:
        return None
    return None

def extract_visit_club_links_from_page(url, verbose=False):
    soup = get_soup(url)
    if not soup: return []
    links = []
    # RX "Visit Club" buttons are <a> with text "Visit Club"
    for a in soup.find_all("a"):
        txt = (a.get_text() or "").strip().lower()
        href = a.get("href") or ""
        if "visit club" in txt and href:
            full = urljoin(BASE, href)
            # try to find club name nearby
            club_name = None
            p = a.find_parent()
            if p:
                h2 = p.find("h2")
                if h2: club_name = (h2.get_text() or "").strip()
            if not club_name:
                prev = a.find_previous(["h2","h3"])
                if prev: club_name = (prev.get_text() or "").strip()
            if verbose: print(f"[CLUB] {club_name or ''} -> {full}")
            links.append((club_name or "", full))
    # de-dupe preserving order
    seen, ordered = set(), []
    for name, href in links:
        if href not in seen:
            seen.add(href); ordered.append((name, href))
    return ordered

def text_after_label(label, text):
    lines = text.splitlines()
    for i, line in enumerate(lines):
        if label.lower() in line.lower():
            for j in range(i+1, min(i+5, len(lines))):
                v = lines[j].strip()
                if v: return v
    return ""

def derive_domain(email):
    try:
        return email.split("@",1)[1].lower()
    except Exception:
        return ""

def scrape_contact_page(club_url, verbose=False):
    contact_url = club_url if club_url.endswith("/contact") else urljoin(club_url.rstrip("/")+"/", "contact")
    soup = get_soup(contact_url)
    if not soup:
        return {"contact_name":"", "email":"", "address":"", "contact_url": contact_url}
    txt = soup.get_text("\n", strip=True)
    contact_name = text_after_label("Contact Name", txt)
    address = text_after_label("Address", txt)
    email = text_after_label("Email", txt)
    if not email:
        m = EMAIL_RE.search(txt)
        if m: email = m.group(0)
    if verbose: print(f"[CONTACT] {club_url} -> name='{contact_name}' email='{email}'")
    return {"contact_name":contact_name, "email":email, "address":address, "contact_url":contact_url}

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--union_slug", help="e.g. texas (uses https://xplorer.rugby/<slug>/clubs)")
    ap.add_argument("--clubs_url", help="Paste the exact RX Clubs page URL (overrides union_slug)")
    ap.add_argument("--out", default="rx_contacts.csv")
    ap.add_argument("--delay", type=float, default=0.7)
    ap.add_argument("--verbose", action="store_true")
    args = ap.parse_args()

    if not args.clubs_url and not args.union_slug:
        raise SystemExit("Provide --clubs_url or --union_slug")

    clubs_page = args.clubs_url or f"{BASE}/{args.union_slug}/clubs"
    if args.verbose: print(f"[INFO] Clubs page: {clubs_page}")

    clubs = extract_visit_club_links_from_page(clubs_page, verbose=args.verbose)
    print(f"[INFO] Found {len(clubs)} clubs.")

    fieldnames = ["Union/Source", "Club Name", "RX Club URL", "RX Contact URL",
                  "Contact Name", "Contact Email", "Club Domain (from email)", "Address"]
    rows = 0
    with open(args.out, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fieldnames)
        w.writeheader(); f.flush()
        for club_name, club_url in clubs:
            data = scrape_contact_page(club_url, verbose=args.verbose)
            w.writerow({
                "Union/Source": clubs_page,
                "Club Name": club_name,
                "RX Club URL": club_url,
                "RX Contact URL": data["contact_url"],
                "Contact Name": data["contact_name"],
                "Contact Email": data["email"],
                "Club Domain (from email)": derive_domain(data["email"]) if data["email"] else "",
                "Address": data["address"]
            })
            f.flush()
            rows += 1
            time.sleep(args.delay)
    print(f"[DONE] Wrote {rows} rows to {args.out}")

if __name__ == "__main__":
    main()
